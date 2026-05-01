from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config import settings


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str | None
    role: str = "authenticated"


_bearer = HTTPBearer(auto_error=False)


def _decode(token: str) -> dict:
    """Decode a Supabase JWT.

    Supabase signs with HS256 + the project's JWT secret. If no secret is
    configured we accept unsigned payloads in development only.
    """
    secret = settings.supabase_service_key
    if secret:
        return jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
    if settings.environment != "development":
        raise JWTError("JWT secret not configured")
    return jwt.get_unverified_claims(token)


async def auth_dependency(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    try:
        payload = _decode(creds.credentials)
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing sub")
    return AuthUser(id=sub, email=payload.get("email"), role=payload.get("role", "authenticated"))


async def optional_auth(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser | None:
    """Returns user when a valid token is present, otherwise None.

    Useful for endpoints that personalize when authenticated but stay public
    for hackathon demos.
    """
    if creds is None or not settings.auth_required:
        return None
    try:
        payload = _decode(creds.credentials)
    except JWTError:
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    return AuthUser(id=sub, email=payload.get("email"), role=payload.get("role", "authenticated"))
