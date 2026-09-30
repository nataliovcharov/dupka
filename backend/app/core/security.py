import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# auto_error off, so every failure gives the same 401 below
bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> None:
    """Let the request through only with the admin token."""
    expected = settings.admin_token.get_secret_value() if settings.admin_token else ""
    given = credentials.credentials if credentials else ""
    # compare_digest takes the same time for any wrong token
    if not expected or not secrets.compare_digest(given.encode(), expected.encode()):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "invalid or missing admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )
