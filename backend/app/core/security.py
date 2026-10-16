import jwt
from typing import Optional
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

class AuthenticatedUser(BaseModel):
    id: str
    email: Optional[str] = None
    role: str = "authenticated"

import logging
import json
import urllib.request
import urllib.error
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

# Initialize PyJWKClient for modern Supabase ES256 / RS256 JWKS tokens
_jwks_client: Optional[PyJWKClient] = None
if settings.SUPABASE_URL:
    try:
        _jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(_jwks_url, cache_jwk_set=True, lifespan=3600)
    except Exception as e:
        logger.warning(f"Could not initialize Supabase PyJWKClient: {e}")

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> AuthenticatedUser:
    """
    Validates Supabase-issued JWT Bearer token server-side.
    Supports modern Supabase ES256 JWKS, standard HS256/RS256 tokens,
    and authoritative verification via Supabase Auth API.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer access token in Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Inspect token header algorithm
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "HS256")
    except Exception:
        alg = "HS256"

    # 1. Asymmetric ES256 / RS256 token verification via Supabase JWKS
    if alg in ["ES256", "RS256"] and _jwks_client:
        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                options={"verify_aud": False}
            )
            user_id = payload.get("sub")
            if user_id:
                return AuthenticatedUser(
                    id=str(user_id),
                    email=payload.get("email"),
                    role=payload.get("role", "authenticated")
                )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.debug(f"JWKS verification failed, trying fallback: {e}")

    # 2. Symmetric HS256 token verification (used in test suite or HMAC secret)
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256", "RS256"],
                options={"verify_aud": False}
            )
            user_id = payload.get("sub")
            if user_id:
                return AuthenticatedUser(
                    id=str(user_id),
                    email=payload.get("email"),
                    role=payload.get("role", "authenticated")
                )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception:
            pass

    # 3. Authoritative verification via Supabase Auth API
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        try:
            req = urllib.request.Request(
                f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {token}",
                }
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    uid = data.get("id")
                    if uid:
                        return AuthenticatedUser(
                            id=str(uid),
                            email=data.get("email"),
                            role=data.get("role", "authenticated")
                        )
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token is invalid or expired. Please sign in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except Exception as e:
            logger.warning(f"Authoritative Supabase check error: {e}")

    # 4. Development mode fallback if debug enabled
    if settings.DEBUG:
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            user_id = unverified_payload.get("sub")
            if user_id:
                return AuthenticatedUser(
                    id=str(user_id),
                    email=unverified_payload.get("email"),
                    role=unverified_payload.get("role", "authenticated")
                )
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token verification failed. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[AuthenticatedUser]:
    """
    Returns AuthenticatedUser if valid Bearer token is provided; returns None if anonymous.
    Allows public or preview uploads while enforcing strict ownership if authenticated.
    """
    if not credentials or not credentials.credentials:
        return None
    return get_current_user(credentials)

