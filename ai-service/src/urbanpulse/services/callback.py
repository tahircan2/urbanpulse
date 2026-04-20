"""
urbanpulse.services.callback — HTTP callback to Spring Boot backend.

Sends pipeline results and agent logs back to the Java backend
after AI processing completes.
"""
from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from urbanpulse.core.config import get_settings
from urbanpulse.core.logging import get_logger
from urbanpulse.models import AgentResultCallback, PipelineResult

logger = get_logger(__name__)


def _headers() -> dict:
    return {
        "Content-Type":      "application/json",
        "X-Internal-Secret": get_settings().internal_secret,
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _post(url: str, payload: dict) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=_headers())
        resp.raise_for_status()


async def send_pipeline_result(result: PipelineResult) -> None:
    """
    1. POST /incidents/{id}/agent-result  → update incident record
    2. POST /agent-logs/batch             → persist agent log rows
    """
    base = get_settings().spring_backend_url.rstrip("/")
    log  = logger.bind(incident_id=result.incident_id)

    callback = AgentResultCallback(
        incident_id=result.incident_id,
        category=result.classified_category,
        priority=result.classified_priority,
        assigned_department=result.assigned_department,
        sla_hours=result.sla_hours,
        agent_notes=result.agent_notes,
        agent_processed=True,
        logs=[],
    )

    try:
        if result.agent_logs:
            await _post(
                f"{base}/agent-logs/batch",
                {"logs": [l.model_dump(mode="json") for l in result.agent_logs]},
            )
            log.info("callback_logs_ok", count=len(result.agent_logs))

        await _post(
            f"{base}/incidents/{result.incident_id}/agent-result",
            callback.model_dump(mode="json"),
        )
        log.info("callback_agent_result_ok")

    except Exception as exc:
        log.error("callback_failed", error=str(exc))
