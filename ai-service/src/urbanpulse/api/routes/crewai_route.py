"""
urbanpulse.api.routes.crewai_route — CrewAI pipeline endpoint.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from urbanpulse.api.dependencies       import verify_internal_secret
from urbanpulse.core.logging            import get_logger
from urbanpulse.models                  import PipelineResult, ProcessIncidentRequest
from urbanpulse.crewai_pipeline.runner  import run_pipeline
from urbanpulse.services.callback       import send_pipeline_result

logger = get_logger(__name__)
router = APIRouter(tags=["CrewAI"])
Auth   = Annotated[None, Depends(verify_internal_secret)]


@router.post(
    "/crewai/process",
    response_model=PipelineResult,
    dependencies=[Depends(verify_internal_secret)],
)
async def process_incident(
    body: ProcessIncidentRequest,
    bg: BackgroundTasks,
) -> PipelineResult:
    """Run Classifier → Planner → Monitor for one incident via CrewAI."""
    log = logger.bind(incident_id=body.incident.id)
    log.info("crewai_process_request", title=body.incident.title)

    try:
        result = await run_pipeline(body.incident)
    except Exception as exc:
        log.error("crewai_pipeline_unhandled_error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}")

    bg.add_task(send_pipeline_result, result)
    return result
