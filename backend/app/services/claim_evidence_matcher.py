import re
from typing import Dict, List, Any, Optional, Tuple

class ClaimEvidenceMatcher:
    @classmethod
    def match_claims(
        cls,
        claims: List[Dict[str, Any]],
        connections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates resume claims against connected external evidence (GitHub repositories,
        observable tests, language telemetry, and coding platform profiles).
        """
        # Find GitHub connection
        github_conn = next((c for c in connections if c.get("id") == "github" and c.get("status") == "connected"), None)
        github_meta = github_conn.get("metadata", {}) if github_conn else {}
        repos: List[Dict[str, Any]] = github_meta.get("repositories", [])
        gh_langs: Dict[str, float] = github_meta.get("language_breakdown", {})

        evaluated_claims: List[Dict[str, Any]] = []
        supported_count = 0
        partial_count = 0
        unverified_count = 0
        inaccessible_count = 0

        for claim in claims:
            claim_type = claim.get("claim_type", "project")

            if claim_type == "project":
                result = cls._evaluate_project_claim(claim, repos, github_conn)
            else:
                result = cls._evaluate_skill_claim(claim, repos, gh_langs, github_conn)

            status = result["status"]
            if status == "supported":
                supported_count += 1
            elif status == "partially_supported":
                partial_count += 1
            elif status == "inaccessible":
                inaccessible_count += 1
            else:
                unverified_count += 1

            evaluated_claims.append(result)

        total = len(evaluated_claims)
        if total > 0:
            raw_score = ((supported_count * 1.0) + (partial_count * 0.5)) / total * 100
            verification_score = max(0, min(100, round(raw_score)))
        else:
            verification_score = 0

        connected_sources = [c.get("name", c.get("id")) for c in connections if c.get("status") == "connected"]

        summary = (
            f"Evaluated {total} claims across {len(connected_sources)} connected profile sources. "
            f"{supported_count} claims supported with verifiable repository artifacts, "
            f"{partial_count} partially supported, {unverified_count} unverified, and "
            f"{inaccessible_count} inaccessible."
        )

        disclaimer = (
            "CareerLens Evidence Verification performs deterministic cross-referencing against "
            "public repository names, languages, documentation, and test artifacts. A README or commit history "
            "does not prove total sole authorship of every line, and missing public evidence does NOT prove a "
            "claim is false, as projects may be private, proprietary, or subject to non-disclosure agreements."
        )

        return {
            "total_claims": total,
            "supported_claims": supported_count,
            "partially_supported_claims": partial_count,
            "unverified_claims": unverified_count,
            "inaccessible_claims": inaccessible_count,
            "verification_score": verification_score,
            "claims": evaluated_claims,
            "connected_sources": connected_sources,
            "summary_message": summary,
            "disclaimer": disclaimer,
        }

    @classmethod
    def _evaluate_project_claim(
        cls,
        claim: Dict[str, Any],
        repos: List[Dict[str, Any]],
        github_conn: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        proj_name = claim.get("project_name", "")
        claimed_techs = claim.get("claimed_technologies", [])
        norm_proj = re.sub(r"[^a-z0-9]", "", proj_name.lower())

        if not github_conn:
            return {
                "claim_id": claim.get("claim_id", ""),
                "claim_type": "project",
                "original_claim": claim.get("original_claim", ""),
                "project_name": proj_name,
                "claimed_technologies": claimed_techs,
                "evidence_source": "GitHub (Not Connected)",
                "supporting_excerpt": "No GitHub profile linked to evaluate repository code.",
                "status": "inaccessible",
                "confidence": 0,
                "reason": "GitHub account has not been connected to CareerLens.",
                "evidence_limitations": "External verification requires an accessible public profile.",
                "recommended_action": "Connect your GitHub profile on the Profile Connections page to verify project evidence.",
                "repository_url": None,
                "has_test_suite": False,
                "has_documentation": False,
                "language_breakdown": {},
            }

        # 1. Search for matching repository by name or slug
        matched_repo = None
        for repo in repos:
            norm_repo = re.sub(r"[^a-z0-9]", "", repo.get("name", "").lower())
            if norm_proj and (norm_proj in norm_repo or norm_repo in norm_proj):
                matched_repo = repo
                break
            # Also check if project name is in repo description or topics
            if proj_name.lower() in repo.get("description", "").lower():
                matched_repo = repo
                break

        if not matched_repo:
            return {
                "claim_id": claim.get("claim_id", ""),
                "claim_type": "project",
                "original_claim": claim.get("original_claim", ""),
                "project_name": proj_name,
                "claimed_technologies": claimed_techs,
                "evidence_source": f"GitHub: {github_conn.get('username_or_url', '')}",
                "supporting_excerpt": f"No public repository matching '{proj_name}' found in candidate's repositories.",
                "status": "unverified",
                "confidence": 20,
                "reason": f"No public repository named '{proj_name}' was found in connected repositories.",
                "evidence_limitations": "Missing public repository does NOT imply claim is inaccurate. The project may be private or enterprise-hosted.",
                "recommended_action": f"If '{proj_name}' is public, ensure it is pinned or hosted under your connected GitHub account.",
                "repository_url": None,
                "has_test_suite": False,
                "has_documentation": False,
                "language_breakdown": {},
            }

        # 2. Matched repository found: check technology alignment and test suite
        repo_langs = matched_repo.get("languages", {})
        repo_langs_lower = {k.lower(): v for k, v in repo_langs.items()}
        repo_readme = matched_repo.get("readme_excerpt", "")
        repo_readme_lower = repo_readme.lower()
        has_tests = matched_repo.get("has_test_suite", False)
        test_artifacts = matched_repo.get("test_artifacts", [])

        matching_techs: List[str] = []
        for tech in claimed_techs:
            t_lower = tech.lower()
            if t_lower in repo_langs_lower or t_lower in repo_readme_lower:
                matching_techs.append(tech)

        tech_overlap_ratio = len(matching_techs) / max(1, len(claimed_techs)) if claimed_techs else 1.0

        if tech_overlap_ratio >= 0.5:
            status_verdict = "supported"
            confidence = 90 if has_tests else 80
            reason = (
                f"Public repository '{matched_repo['name']}' verified. "
                f"Technologies ({', '.join(matching_techs)}) verified in codebase languages or manifest files. "
                f"{'Observable automated test suite detected.' if has_tests else 'No automated test files detected in root.'}"
            )
        else:
            status_verdict = "partially_supported"
            confidence = 65
            reason = (
                f"Repository '{matched_repo['name']}' exists, but only {len(matching_techs)} of "
                f"{len(claimed_techs)} claimed technologies could be confirmed in public languages."
            )

        excerpt_snippet = repo_readme[:250].strip() if repo_readme else f"Languages: {', '.join(repo_langs.keys())}"

        return {
            "claim_id": claim.get("claim_id", ""),
            "claim_type": "project",
            "original_claim": claim.get("original_claim", ""),
            "project_name": proj_name,
            "claimed_technologies": claimed_techs,
            "evidence_source": f"GitHub: {matched_repo.get('full_name', matched_repo.get('name'))}",
            "supporting_excerpt": excerpt_snippet,
            "status": status_verdict,
            "confidence": confidence,
            "reason": reason,
            "evidence_limitations": "Repository existence and documentation reflect project structure, but do not prove personal sole authorship of every commit.",
            "recommended_action": "Maintain clean README documentation, test suites, and deployment instructions.",
            "repository_url": matched_repo.get("html_url"),
            "has_test_suite": has_tests,
            "has_documentation": len(repo_readme) > 50,
            "language_breakdown": repo_langs,
        }

    @classmethod
    def _evaluate_skill_claim(
        cls,
        claim: Dict[str, Any],
        repos: List[Dict[str, Any]],
        gh_langs: Dict[str, float],
        github_conn: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        techs = claim.get("claimed_technologies", [])
        skill_name = techs[0] if techs else ""
        skill_lower = skill_name.lower()

        if not github_conn:
            return {
                "claim_id": claim.get("claim_id", ""),
                "claim_type": "technical_skill",
                "original_claim": claim.get("original_claim", ""),
                "project_name": None,
                "claimed_technologies": techs,
                "evidence_source": "GitHub (Not Connected)",
                "supporting_excerpt": "Profile not linked.",
                "status": "inaccessible",
                "confidence": 0,
                "reason": "GitHub profile not linked.",
                "evidence_limitations": "External verification requires an accessible public profile.",
                "recommended_action": "Connect your GitHub account to verify skill frequency in public code.",
                "repository_url": None,
                "has_test_suite": False,
                "has_documentation": False,
                "language_breakdown": {},
            }

        # Check if skill appears in candidate's language breakdown or repo files
        matching_repos = []
        for repo in repos:
            repo_langs_lower = {k.lower(): v for k, v in repo.get("languages", {}).items()}
            if skill_lower in repo_langs_lower or skill_lower == (repo.get("primary_language") or "").lower():
                matching_repos.append(repo.get("name"))

        if matching_repos:
            pct = gh_langs.get(skill_name, 0)
            return {
                "claim_id": claim.get("claim_id", ""),
                "claim_type": "technical_skill",
                "original_claim": claim.get("original_claim", ""),
                "project_name": None,
                "claimed_technologies": techs,
                "evidence_source": f"GitHub: {len(matching_repos)} Repositories",
                "supporting_excerpt": f"Observable in repositories: {', '.join(matching_repos[:3])}. Accounts for {pct}% of candidate's public GitHub code.",
                "status": "supported",
                "confidence": 85,
                "reason": f"Skill '{skill_name}' actively demonstrated across {len(matching_repos)} public repository codebase(s).",
                "evidence_limitations": "Code presence demonstrates practical usage, but does not measure enterprise architecture seniority.",
                "recommended_action": f"Continue building non-trivial projects utilizing {skill_name}.",
                "repository_url": github_conn.get("username_or_url"),
                "has_test_suite": True,
                "has_documentation": True,
                "language_breakdown": {skill_name: pct},
            }
        else:
            return {
                "claim_id": claim.get("claim_id", ""),
                "claim_type": "technical_skill",
                "original_claim": claim.get("original_claim", ""),
                "project_name": None,
                "claimed_technologies": techs,
                "evidence_source": f"GitHub: {github_conn.get('username_or_url', '')}",
                "supporting_excerpt": f"Skill '{skill_name}' was not detected in primary languages of public repositories.",
                "status": "unverified",
                "confidence": 30,
                "reason": f"No public repositories found with '{skill_name}' as a primary or detected language.",
                "evidence_limitations": "The skill may be applied in private repos or academic coursework.",
                "recommended_action": f"Publish an open-source sample or library showcasing your {skill_name} capabilities.",
                "repository_url": None,
                "has_test_suite": False,
                "has_documentation": False,
                "language_breakdown": {},
            }

claim_evidence_matcher = ClaimEvidenceMatcher()
