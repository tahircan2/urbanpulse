"""
urbanpulse.langgraph_pipeline.state — Pipeline state schema.

Defines the typed state that flows through every LangGraph node.
"""
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage


class PipelineState(TypedDict):
    """Typed state flowing through the LangGraph pipeline."""

    # ── Input ─────────────────────────────────────────────────────────────
    incident: dict                    # Raw incident data (model_dump)
    consistency_warning: str          # From validator

    # ── Guardrails ────────────────────────────────────────────────────────
    input_safe: bool
    input_reason: str

    # ── Classifier output ─────────────────────────────────────────────────
    category: str
    priority: int
    confidence: float
    reasoning: str
    override_reason: str

    # ── Planner output ────────────────────────────────────────────────────
    department: str
    sla_hours: int
    action_note: str

    # ── Monitor output ────────────────────────────────────────────────────
    summary: str

    # ── Output guardrail ──────────────────────────────────────────────────
    output_safe: bool
    agent_notes: str

    # ── Metadata ──────────────────────────────────────────────────────────
    elapsed_ms: int
    success: bool
    error: str

    # ── Internal LangGraph message state (for tool calling if needed) ─────
    messages: Annotated[Sequence[BaseMessage], operator.add]
