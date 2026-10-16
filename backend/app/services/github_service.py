import re
import urllib.parse
import datetime
import base64
from typing import Dict, List, Any, Optional, Tuple
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

GITHUB_USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$")
ALLOWED_GITHUB_HOSTS = {"github.com", "www.github.com", "api.github.com"}

TEST_FILE_PATTERNS = re.compile(
    r"(^tests?$|^__tests__$|^test_.*|.*[._]test\..*|.*[._]spec\..*)",
    re.IGNORECASE
)

CONFIG_FILE_PATTERNS = re.compile(
    r"(package\.json|requirements\.txt|pyproject\.toml|dockerfile|docker-compose\.ya?ml|go\.mod|cargo\.toml|\.github)",
    re.IGNORECASE
)

class GitHubService:
    def __init__(self):
        # In-memory cache: username -> (cache_timestamp, profile_data)
        self._cache: Dict[str, Tuple[datetime.datetime, Dict[str, Any]]] = {}
        self._cache_ttl_seconds = 900  # 15 minutes

    @staticmethod
    def extract_and_validate_username(input_val: str) -> str:
        """
        Extracts and rigorously validates a GitHub username from either a raw username
        or a public profile URL (e.g., https://github.com/octocat).
        Blocks SSRF and invalid hosts.
        """
        if not input_val or not input_val.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub handle or profile URL must not be empty."
            )

        clean = input_val.strip()

        # Check if URL was supplied
        if clean.startswith("http://") or clean.startswith("https://") or "github.com/" in clean:
            if not clean.startswith("http://") and not clean.startswith("https://"):
                clean = "https://" + clean
            try:
                parsed = urllib.parse.urlparse(clean)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Malformed URL provided for GitHub profile."
                )

            hostname = (parsed.hostname or "").lower()
            if hostname not in ALLOWED_GITHUB_HOSTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Security violation: Only official GitHub hosts are permitted (got '{hostname}')."
                )

            path_parts = [p for p in parsed.path.strip("/").split("/") if p]
            if not path_parts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="GitHub profile URL does not contain a username path."
                )
            username = path_parts[0]
        else:
            # Raw username with optional @ prefix
            username = clean.lstrip("@")

        if not GITHUB_USERNAME_REGEX.match(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid GitHub username '{username}'. Usernames must be 1-39 alphanumeric characters and may contain single hyphens."
            )

        return username

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CareerLens-Employability-Verifier/1.0",
        }
        if settings.GITHUB_TOKEN and settings.GITHUB_TOKEN.strip():
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN.strip()}"
        return headers

    def fetch_user_profile_and_repos(
        self,
        username_or_url: str,
        max_repos: int = 10,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Fetches public repositories, language distribution, README excerpts, and test artifacts
        for a validated GitHub user using the official GitHub REST API.
        """
        username = self.extract_and_validate_username(username_or_url)
        now = datetime.datetime.now(datetime.timezone.utc)

        # Check cache
        if not force_refresh and username in self._cache:
            cached_time, cached_data = self._cache[username]
            if (now - cached_time).total_seconds() < self._cache_ttl_seconds:
                return cached_data

        headers = self._get_headers()
        timeout = settings.GITHUB_API_TIMEOUT

        try:
            with httpx.Client(timeout=timeout) as client:
                # 1. Fetch User Profile
                user_res = client.get(f"https://api.github.com/users/{username}", headers=headers)
                if user_res.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"GitHub user '{username}' not found. Please verify the handle."
                    )
                elif user_res.status_code == 403:
                    reset_ts = user_res.headers.get("x-ratelimit-reset", "")
                    reset_msg = ""
                    if reset_ts:
                        try:
                            reset_dt = datetime.datetime.fromtimestamp(int(reset_ts), tz=datetime.timezone.utc)
                            reset_msg = f" Rate limit resets at {reset_dt.strftime('%H:%M:%S UTC')}."
                        except Exception:
                            pass
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"GitHub API public rate limit reached.{reset_msg} Configure GITHUB_TOKEN in settings for 5000 requests/hr."
                    )
                elif user_res.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"GitHub API returned unexpected status {user_res.status_code}."
                    )

                user_data = user_res.json()

                # 2. Fetch User Public Repositories (sorted by recently pushed/updated)
                repos_res = client.get(
                    f"https://api.github.com/users/{username}/repos",
                    params={"sort": "updated", "per_page": max_repos, "type": "public"},
                    headers=headers
                )
                if repos_res.status_code != 200:
                    repos_list = []
                else:
                    repos_list = repos_res.json()

                detailed_repos: List[Dict[str, Any]] = []
                aggregate_languages: Dict[str, int] = {}

                for repo in repos_list[:max_repos]:
                    repo_name = repo.get("name", "")
                    repo_owner = repo.get("owner", {}).get("login", username)

                    # Fetch languages for repo
                    languages_map: Dict[str, int] = {}
                    try:
                        lang_res = client.get(
                            f"https://api.github.com/repos/{repo_owner}/{repo_name}/languages",
                            headers=headers
                        )
                        if lang_res.status_code == 200:
                            languages_map = lang_res.json()
                            for l_name, l_bytes in languages_map.items():
                                aggregate_languages[l_name] = aggregate_languages.get(l_name, 0) + l_bytes
                    except Exception:
                        languages_map = {repo.get("language"): 1000} if repo.get("language") else {}

                    # Fetch README excerpt
                    readme_excerpt = ""
                    try:
                        readme_headers = {**headers, "Accept": "application/vnd.github.v3.raw"}
                        readme_res = client.get(
                            f"https://api.github.com/repos/{repo_owner}/{repo_name}/readme",
                            headers=readme_headers
                        )
                        if readme_res.status_code == 200:
                            readme_excerpt = readme_res.text[:1500]
                    except Exception:
                        readme_excerpt = ""

                    # Inspect root contents for tests, CI, and config manifests
                    has_tests = False
                    test_files: List[str] = []
                    config_artifacts: List[str] = []
                    try:
                        contents_res = client.get(
                            f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents",
                            headers=headers
                        )
                        if contents_res.status_code == 200:
                            for item in contents_res.json():
                                item_name = item.get("name", "")
                                if TEST_FILE_PATTERNS.search(item_name):
                                    has_tests = True
                                    test_files.append(item_name)
                                if CONFIG_FILE_PATTERNS.search(item_name):
                                    config_artifacts.append(item_name)
                    except Exception:
                        pass

                    detailed_repos.append({
                        "name": repo_name,
                        "full_name": repo.get("full_name", f"{username}/{repo_name}"),
                        "description": repo.get("description") or "No description provided.",
                        "html_url": repo.get("html_url", f"https://github.com/{username}/{repo_name}"),
                        "primary_language": repo.get("language") or "Text",
                        "languages": languages_map,
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "default_branch": repo.get("default_branch", "main"),
                        "updated_at": repo.get("updated_at", ""),
                        "readme_excerpt": readme_excerpt,
                        "has_test_suite": has_tests,
                        "test_artifacts": test_files[:5],
                        "config_artifacts": config_artifacts[:5],
                        "topics": repo.get("topics", []),
                    })

                # Calculate primary language percentages
                total_bytes = sum(aggregate_languages.values())
                language_percentages = {}
                if total_bytes > 0:
                    for lang, byte_count in sorted(aggregate_languages.items(), key=lambda x: x[1], reverse=True)[:6]:
                        language_percentages[lang] = round((byte_count / total_bytes) * 100, 1)

                result = {
                    "username": username,
                    "name": user_data.get("name") or username,
                    "html_url": user_data.get("html_url", f"https://github.com/{username}"),
                    "avatar_url": user_data.get("avatar_url", ""),
                    "bio": user_data.get("bio") or "",
                    "public_repos_count": user_data.get("public_repos", len(detailed_repos)),
                    "followers_count": user_data.get("followers", 0),
                    "created_at": user_data.get("created_at", ""),
                    "repositories": detailed_repos,
                    "language_breakdown": language_percentages,
                    "retrieved_at": now.isoformat(),
                    "status": "connected",
                }

                self._cache[username] = (now, result)
                return result

        except HTTPException:
            raise
        except (httpx.ConnectError, httpx.TimeoutException) as net_err:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"GitHub connection timed out or failed to connect: {str(net_err)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error while communicating with GitHub: {str(e)}"
            )

github_service = GitHubService()
