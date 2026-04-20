"""
urbanpulse.langgraph_pipeline.nodes.rejected — Rejection terminal node.

Produces a failure result when the input guardrail rejects the incident.
"""
from __future__ import annotations

from urbanpulse.langgraph_pipeline.state import PipelineState


def rejected_node(state: PipelineState) -> dict:
    """Return a rejection result when input is flagged as unsafe."""
    return {
        "success":     False,
        "error":       state.get("input_reason", "Rejected by input guardrail"),
        "agent_notes": f"Güvenlik İhlali: {state.get('input_reason')}",
        "category":    state["incident"].get("category", "OTHER"),
        "priority":    state["incident"].get("priority", 3),
        "department":  "None",
        "sla_hours":   0,
    }
