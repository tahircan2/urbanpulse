"""
urbanpulse.api.routes.health — Health-check endpoint.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from urbanpulse.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment="production",
        agents=["CLASSIFIER", "PLANNER", "MONITOR", "LANGGRAPH"],
        timestamp=datetime.now(timezone.utc),
    )
