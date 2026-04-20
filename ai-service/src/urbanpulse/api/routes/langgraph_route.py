"""
urbanpulse.api.routes.langgraph_route — LangGraph pipeline endpoint.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from urbanpulse.api.dependencies            import verify_internal_secret
from urbanpulse.core.logging                 import get_logger
from urbanpulse.models                       import PipelineResult, ProcessIncidentRequest
from urbanpulse.langgraph_pipeline.runner    import run_langgraph_pipeline
from urbanpulse.services.callback            import send_pipeline_result

logger = get_logger(__name__)
router = APIRouter(tags=["LangGraph"])


@router.post(
    "/pipeline/process",
    response_model=PipelineResult,
    dependencies=[Depends(verify_internal_secret)],
)
async def process_incident_langgraph(
    body: ProcessIncidentRequest,
    bg: BackgroundTasks,
) -> PipelineResult:
    """Run Input Guard → Classifier → Planner → Monitor → Output Guard via LangGraph."""
    log = logger.bind(incident_id=body.incident.id)
    log.info("langgraph_process_request", title=body.incident.title)

    try:
        result = await run_langgraph_pipeline(body.incident)
    except Exception as exc:
        log.error("langgraph_pipeline_unhandled_error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}")

    bg.add_task(send_pipeline_result, result)
    return result
