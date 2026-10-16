import ipaddress
import re
import socket
import urllib.parse
from typing import Tuple
import httpx
from fastapi import HTTPException, status

BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}

class SafeURLRetriever:
    @classmethod
    def fetch_job_text_from_url(cls, url: str) -> str:
        """
        Safely fetches and converts remote job description HTML into plain text.
        Guards against SSRF, internal network scanning, and authentication bypass.
        """
        if not url or not url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No URL provided."
            )

        parsed = urllib.parse.urlparse(url.strip())
        if parsed.scheme not in ["http", "https"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported URL protocol '{parsed.scheme}'. Only standard HTTP and HTTPS URLs are permitted."
            )

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL: missing host name."
            )

        # 1. SSRF Guard: block localhost and private IP addresses
        if hostname.lower() in BLOCKED_HOSTNAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security restriction: access to local and loopback addresses is blocked."
            )

        try:
            # Resolve DNS to check IP range
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security restriction: access to internal private network addresses is forbidden."
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to resolve domain '{hostname}': {str(e)}"
            )

        # 2. Perform HTTP request with timeout and standard browser headers
        headers = {
            "User-Agent": "CareerLensJobMatcher/1.0 (Mozilla/5.0 compatible; Research Parser)"
        }

        try:
            with httpx.Client(timeout=6.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)

                if response.status_code in [401, 403]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Remote job posting is protected by a login wall or access control (HTTP {response.status_code}). "
                            "CareerLens does not bypass authentication. Please copy and paste the job description text directly."
                        )
                    )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to retrieve job description from URL: HTTP status {response.status_code}."
                    )

                html_content = response.text
                if not html_content or len(html_content.strip()) < 50:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Retrieved URL page returned empty or insufficient content."
                    )

                # Extract readable text from HTML
                return cls._extract_text_from_html(html_content)

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Connection timed out while attempting to reach job description URL. Please paste text directly."
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Network error accessing job URL: {str(e)}. Please paste job description text directly."
            )

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """
        Strips script, style, navigation, and tags to extract plain text.
        """
        # Strip script and style blocks
        no_scripts = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        # Strip HTML tags
        no_tags = re.sub(r"<[^>]+>", "\n", no_scripts)
        # Decode common HTML entities
        clean = (
            no_tags.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )
        # Collapse excessive whitespace
        lines = [line.strip() for line in clean.splitlines() if len(line.strip()) > 3]
        return "\n".join(lines)

url_retriever = SafeURLRetriever()
