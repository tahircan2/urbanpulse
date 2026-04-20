"""
urbanpulse.crewai_pipeline.runner — Pipeline execution logic.

Orchestrates: Input Guard → CrewAI Crew → Output Guard → PipelineResult.
Extracted from the original monolithic crew.py for single-responsibility.
"""
from __future__ import annotations

import asyncio
import json
import time

from urbanpulse.core.config  import get_settings
from urbanpulse.core.logging import get_logger
from urbanpulse.guardrails   import check_input_guard, check_output_guard
from urbanpulse.models import (
    AgentAction,
    AgentLogCreate,
    AgentName,
    IncidentCategory,
    IncidentDTO,
    PipelineResult,
)
from urbanpulse.services.validator    import check_content_consistency
from urbanpulse.crewai_pipeline.crew  import UrbanPulseCrew

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_AGENT_NOTES: int = 500
MAX_SLA_HOURS:   int = 720


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    """Extract JSON from LLM output, stripping markdown fences if present."""
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        s, e = clean.find("{"), clean.rfind("}") + 1
        if s != -1 and e > s:
            return json.loads(clean[s:e])
        return {}


def _extract_classifier_result(task_output) -> dict:
    """Parse classifier JSON output into a flat dict with safe defaults."""
    data = _parse_json(task_output.raw)
    return {
        "category":        data.get("category", ""),
        "priority":        data.get("priority", 0),
        "confidence":      float(data.get("confidence", 0.75)),
        "reasoning":       str(data.get("reasoning", "")),
        "override_reason": str(data.get("override_reason", "")),
    }


def _extract_planner_result(task_output) -> dict:
    """Parse planner JSON output into a flat dict with safe defaults."""
    data = _parse_json(task_output.raw)
    return {
        "department":  str(data.get("department", "General Municipal Services")),
        "sla_hours":   max(1, min(MAX_SLA_HOURS, int(data.get("sla_hours", 24)))),
        "action_note": str(data.get("action_note", "")),
    }


def _build_agent_logs(
    incident: IncidentDTO,
    clf: dict,
    plan: dict,
    summary: str,
    category: IncidentCategory,
    elapsed_ms: int,
) -> list[AgentLogCreate]:
    """Build the three AgentLogCreate entries for one pipeline run."""
    return [
        AgentLogCreate(
            incident_id=incident.id, incident_title=incident.title,
            agent_name=AgentName.CLASSIFIER, action=AgentAction.CLASSIFY,
            input_summary=f"Cat:{incident.category.value} P{incident.priority} {incident.district}",
            output_summary=f"→ {category.value} P{clf['priority']} ({clf['confidence']:.0%})",
            confidence=clf["confidence"], processing_ms=elapsed_ms, success=True,
            override_reason=clf["override_reason"] or None,
        ),
        AgentLogCreate(
            incident_id=incident.id, incident_title=incident.title,
            agent_name=AgentName.PLANNER, action=AgentAction.ROUTE_TO_DEPARTMENT,
            input_summary=f"Cat:{category.value} P{clf['priority']}",
            output_summary=f"→ {plan['department']} SLA {plan['sla_hours']}h",
            processing_ms=elapsed_ms, success=True,
        ),
        AgentLogCreate(
            incident_id=incident.id, incident_title=incident.title,
            agent_name=AgentName.MONITOR, action=AgentAction.GENERATE_REPORT,
            input_summary="Pipeline complete",
            output_summary=summary[:200],
            processing_ms=elapsed_ms, success=True,
        ),
    ]


def _incident_inputs(incident: IncidentDTO) -> dict:
    """Build crewAI inputs dict, including content-consistency warning."""
    consistency = check_content_consistency(incident)
    consistency_warning = consistency["warning"] if not consistency["consistent"] else ""
    return {
        "incident_id":          incident.id,
        "title":                incident.title,
        "description":          incident.description,
        "category":             incident.category.value,
        "priority":             incident.priority,
        "district":             incident.district,
        "latitude":             incident.latitude,
        "longitude":            incident.longitude,
        "reporter_name":        incident.reporter_name,
        "reporter_email":       incident.reporter_email or "not provided",
        "consistency_warning":  consistency_warning,
    }


# ── Public API ────────────────────────────────────────────────────────────────

async def run_pipeline(incident: IncidentDTO) -> PipelineResult:
    """Run Classifier → Planner → Monitor for one incident."""
    log = logger.bind(incident_id=incident.id)
    log.info("pipeline_start", title=incident.title)
    t0 = int(time.monotonic() * 1000)

    # --- 1. INPUT GUARDRAIL ---
    in_tokens = 0
    try:
        is_safe, reason, in_tokens = await asyncio.to_thread(check_input_guard, incident)
        if not is_safe:
            log.warning("input_guardrail_rejected", reason=reason, tokens=in_tokens)
            return PipelineResult(
                incident_id=incident.id, classified_category=incident.category,
                classified_priority=incident.priority, assigned_department="System Rejected",
                sla_hours=0, agent_notes=f"Güvenlik İhlali: {reason}",
                agent_logs=[], success=False, error=reason,
            )
    except Exception as e:
        log.error("input_guard_error", error=str(e))

    # --- 2. CREW EXECUTION ---
    try:
        out = await asyncio.to_thread(
            lambda: UrbanPulseCrew().crew().kickoff(inputs=_incident_inputs(incident))
        )
        task_outputs = out.tasks_output

        clf     = _extract_classifier_result(task_outputs[0])
        plan    = _extract_planner_result(task_outputs[1])
        summary = task_outputs[2].raw.strip()[:200]

        try:
            category = IncidentCategory(clf["category"])
        except ValueError:
            category = incident.category

        priority    = max(1, min(5, int(clf["priority"] or incident.priority)))
        elapsed_ms  = int(time.monotonic() * 1000) - t0

        logs = _build_agent_logs(incident, clf, plan, summary, category, elapsed_ms)

        agent_notes = " | ".join(
            filter(None, [clf["reasoning"], plan["action_note"], summary])
        )[:MAX_AGENT_NOTES]

        # --- 3. OUTPUT GUARDRAIL ---
        out_tokens = 0
        try:
            out_safe, out_reason, out_tokens = await asyncio.to_thread(
                check_output_guard, agent_notes
            )
            if not out_safe:
                log.warning("output_guardrail_rejected", reason=out_reason, tokens=out_tokens)
                agent_notes = (
                    "Sistem Güvenlik Uyarısı: Üretilen AI çıktısı "
                    "zararlı içerik tespiti sebebiyle gizlendi."
                )
        except Exception as e:
            log.error("output_guard_error", error=str(e))

        # Token tracker
        total_guard_tokens = in_tokens + out_tokens
        logger.info(
            "guardrails_token_usage",
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total=total_guard_tokens,
        )

        log.info(
            "pipeline_complete",
            category=category.value,
            priority=priority,
            department=plan["department"],
            sla_hours=plan["sla_hours"],
            ms=elapsed_ms,
        )

        return PipelineResult(
            incident_id=incident.id,
            classified_category=category,
            classified_priority=priority,
            assigned_department=plan["department"],
            sla_hours=plan["sla_hours"],
            agent_notes=agent_notes,
            agent_logs=logs,
            success=True,
        )

    except Exception as exc:
        log.error("pipeline_error", error=str(exc), incident_id=incident.id)
        return PipelineResult(
            incident_id=incident.id,
            classified_category=incident.category,
            classified_priority=incident.priority,
            assigned_department="General Municipal Services",
            sla_hours=24,
            agent_notes=f"Pipeline hatası: {type(exc).__name__}: {exc}",
            agent_logs=[],
            success=False,
            error=str(exc),
        )
