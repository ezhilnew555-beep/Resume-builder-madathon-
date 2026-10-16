import time
import jwt
import httpx
from typing import Optional, Dict, Any, List
import logging
from app.core.config import settings

logger = logging.getLogger("careerlens_supabase")

class SupabaseService:
    """
    Manages interaction with Supabase PostgreSQL and PostgREST API.
    Operates strictly within Row Level Security rules using user Bearer token
    or server-side service role key where configured.
    """

    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.url and (self.anon_key or self.service_key))

    def get_service_jwt(self) -> str:
        """
        Returns a valid 3-part service_role JWT. If SUPABASE_SERVICE_ROLE_KEY is already
        a JWT, uses it; otherwise cryptographically generates one using SUPABASE_JWT_SECRET.
        """
        if self.service_key and self.service_key.count(".") == 2:
            return self.service_key
        if settings.SUPABASE_JWT_SECRET:
            now = int(time.time())
            return jwt.encode(
                {
                    "role": "service_role",
                    "iss": "supabase",
                    "iat": now,
                    "exp": now + 3600 * 24 * 365,
                },
                settings.SUPABASE_JWT_SECRET,
                algorithm="HS256"
            )
        return self.anon_key or ""

    def get_auth_headers(self, user_token: Optional[str] = None) -> Dict[str, str]:
        """
        Builds headers respecting RLS. When user_token is passed, PostgREST executes queries
        under the authenticated student's identity (`auth.uid() = user_id`).
        Otherwise falls back to service role JWT or anon key.
        """
        headers = {
            "apikey": self.anon_key or "",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"
        else:
            srv_jwt = self.get_service_jwt()
            if srv_jwt:
                headers["Authorization"] = f"Bearer {srv_jwt}"
        return headers

    async def get_profile(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.is_configured:
            return None

        async with httpx.AsyncClient(timeout=5.0) as client:
            endpoint = f"{self.url}/rest/v1/profiles?id=eq.{user_id}&select=*"
            response = await client.get(endpoint, headers=self.get_auth_headers(user_token))
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
            return None

    async def upsert_profile(self, user_id: str, profile_data: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.is_configured:
            return None

        payload = {**profile_data, "id": user_id}
        async with httpx.AsyncClient(timeout=5.0) as client:
            endpoint = f"{self.url}/rest/v1/profiles?on_conflict=id"
            headers = self.get_auth_headers(user_token)
            headers["Prefer"] = "resolution=merge-duplicates,return=representation"
            response = await client.post(endpoint, json=payload, headers=headers)
            if response.status_code in (200, 201):
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
            elif response.status_code == 204:
                return await self.get_profile(user_id, user_token)
            else:
                logger.warning(f"Upsert profile failed ({response.status_code}): {response.text}")
            return None

    async def get_user_reports(self, user_id: str, user_token: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []

        async with httpx.AsyncClient(timeout=5.0) as client:
            endpoint = f"{self.url}/rest/v1/analysis_reports?user_id=eq.{user_id}&select=*"
            response = await client.get(endpoint, headers=self.get_auth_headers(user_token))
            if response.status_code == 200:
                return response.json()
            return []

    async def get_user_job_descriptions(self, user_id: str, user_token: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []

        async with httpx.AsyncClient(timeout=5.0) as client:
            endpoint = f"{self.url}/rest/v1/job_descriptions?user_id=eq.{user_id}&select=*"
            response = await client.get(endpoint, headers=self.get_auth_headers(user_token))
            if response.status_code == 200:
                return response.json()
            return []

    async def create_job_description(self, user_id: str, data: Dict[str, Any], user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.is_configured:
            return None

        payload = {**data, "user_id": user_id}
        async with httpx.AsyncClient(timeout=5.0) as client:
            endpoint = f"{self.url}/rest/v1/job_descriptions"
            headers = self.get_auth_headers(user_token)
            response = await client.post(endpoint, json=payload, headers=headers)
            if response.status_code in (200, 201):
                res_data = response.json()
                if res_data and len(res_data) > 0:
                    return res_data[0]
            return None

supabase_service = SupabaseService()
