"""
urbanpulse.langgraph_pipeline.runner — LangGraph pipeline execution.

Orchestrates state initialisation, graph invocation, and result mapping.
"""
from __future__ import annotations

import asyncio
import time

from urbanpulse.core.logging import get_logger
from urbanpulse.models import (
    AgentAction,
    AgentLogCreate,
    AgentName,
    IncidentCategory,
    IncidentDTO,
    PipelineResult,
)
from urbanpulse.services.validator import check_content_consistency
from urbanpulse.langgraph_pipeline.graph import compiled_graph
from urbanpulse.langgraph_pipeline.state import PipelineState

logger = get_logger(__name__)


async def run_langgraph_pipeline(incident: IncidentDTO) -> PipelineResult:
    """Run the LangGraph pipeline."""
    log = logger.bind(incident_id=incident.id)
    log.info("langgraph_pipeline_start", title=incident.title)
    t0 = int(time.monotonic() * 1000)

    consistency = check_content_consistency(incident)
    warning = consistency["warning"] if not consistency["consistent"] else ""

    state: PipelineState = {
        "incident":             incident.model_dump(),
        "consistency_warning":  warning,
        "input_safe":           True,
        "input_reason":         "",
        "category":             incident.category.value,
        "priority":             incident.priority,
        "confidence":           1.0,
        "reasoning":            "",
        "override_reason":      "",
        "department":           "General Municipal Services",
        "sla_hours":            24,
        "action_note":          "",
        "summary":              "",
        "output_safe":          True,
        "agent_notes":          "",
        "elapsed_ms":           0,
        "success":              True,
        "error":                "",
        "messages":             [],
    }

    try:
        final_state = await asyncio.to_thread(compiled_graph.invoke, state)
        elapsed_ms = int(time.monotonic() * 1000) - t0

        # Check for rejection
        if not final_state.get("success", False) and "error" in final_state:
            return PipelineResult(
                incident_id=incident.id,
                classified_category=incident.category,
                classified_priority=incident.priority,
                assigned_department=final_state.get("department", "System Rejected"),
                sla_hours=final_state.get("sla_hours", 0),
                agent_notes=final_state.get("agent_notes", final_state.get("error", "Error")),
                agent_logs=[],
                success=False,
                error=final_state.get("error"),
            )

        # Parse category
        try:
            category = IncidentCategory(final_state["category"])
        except (ValueError, KeyError):
            category = incident.category

        priority = final_state.get("priority", incident.priority)

        # Build agent logs
        logs = [
            AgentLogCreate(
                incident_id=incident.id,
                incident_title=incident.title,
                agent_name=AgentName.CLASSIFIER,
                action=AgentAction.CLASSIFY,
                input_summary="LangGraph Classification",
                output_summary=f"→ {category.value} P{priority}",
                confidence=final_state.get("confidence", 0.75),
                processing_ms=elapsed_ms,
                success=True,
                override_reason=final_state.get("override_reason") or None,
            ),
            AgentLogCreate(
                incident_id=incident.id,
                incident_title=incident.title,
                agent_name=AgentName.PLANNER,
                action=AgentAction.ROUTE_TO_DEPARTMENT,
                input_summary="LangGraph Planning",
                output_summary=f"→ {final_state.get('department')} SLA {final_state.get('sla_hours')}h",
                processing_ms=elapsed_ms,
                success=True,
            ),
            AgentLogCreate(
                incident_id=incident.id,
                incident_title=incident.title,
                agent_name=AgentName.MONITOR,
                action=AgentAction.GENERATE_REPORT,
                input_summary="LangGraph Pipeline complete",
                output_summary=final_state.get("summary", "")[:200],
                processing_ms=elapsed_ms,
                success=True,
            ),
        ]

        log.info(
            "langgraph_pipeline_complete",
            category=category.value,
            priority=priority,
            department=final_state.get("department"),
            ms=elapsed_ms,
        )

        return PipelineResult(
            incident_id=incident.id,
            classified_category=category,
            classified_priority=priority,
            assigned_department=final_state.get("department", "General Services"),
            sla_hours=final_state.get("sla_hours", 24),
            agent_notes=final_state.get("agent_notes", "Processed by LangGraph"),
            agent_logs=logs,
            success=True,
        )

    except Exception as exc:
        log.error("langgraph_pipeline_error", error=str(exc))
        return PipelineResult(
            incident_id=incident.id,
            classified_category=incident.category,
            classified_priority=incident.priority,
            assigned_department="General Municipal Services",
            sla_hours=24,
            agent_notes=f"Pipeline error: {exc}",
            agent_logs=[],
            success=False,
            error=str(exc),
        )
