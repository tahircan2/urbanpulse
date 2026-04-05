from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from urbanpulse.crew       import run_pipeline
from app.core.logging      import get_logger
from app.core.security     import verify_internal_secret
from app.models.schemas import (
    HealthResponse, PipelineResult, ProcessIncidentRequest,
)
from app.utils.callback import send_pipeline_result

logger = get_logger(__name__)
router = APIRouter()
Auth   = Annotated[None, Depends(verify_internal_secret)]


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment="production",
        agents=["CLASSIFIER", "PLANNER", "MONITOR"],
        timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/pipeline/process",
    response_model=PipelineResult,
    status_code=status.HTTP_200_OK,
    tags=["pipeline"],
    dependencies=[Depends(verify_internal_secret)],
)
async def process_incident(body: ProcessIncidentRequest, bg: BackgroundTasks) -> PipelineResult:
    """Run Classifier → Planner → Monitor for one incident."""
    log = logger.bind(incident_id=body.incident.id)
    log.info("process_request_received", title=body.incident.title)

    try:
        result = await run_pipeline(body.incident)
    except Exception as exc:
        log.error("pipeline_unhandled_error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}")
    bg.add_task(send_pipeline_result, result)
    return result


