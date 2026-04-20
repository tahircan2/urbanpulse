"""
urbanpulse.api.dependencies — Shared FastAPI dependency injections.

Security, authentication, and other cross-cutting request dependencies.
"""
import secrets
from fastapi import Header, HTTPException, status
from urbanpulse.core.config import get_settings


async def verify_internal_secret(
    x_internal_secret: str = Header(..., alias="X-Internal-Secret"),
) -> None:
    """Validates the shared secret sent by Spring Boot on every AI callback."""
    if not secrets.compare_digest(x_internal_secret, get_settings().internal_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal secret",
        )
