"""
urbanpulse.langgraph_pipeline.nodes.monitor — Pipeline summary node.

Produces a concise one-line summary of the pipeline result.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from urbanpulse.core.config import get_settings
from urbanpulse.core.logging import get_logger
from urbanpulse.langgraph_pipeline.state import PipelineState
from urbanpulse.langgraph_pipeline.nodes.utils import get_llm

logger = get_logger(__name__)

def monitor_node(state: PipelineState) -> dict:
    """Summarise the pipeline result in a single concise English sentence."""
    inc = state["incident"]
    logger.info("node_start", node="monitor", incident_id=inc.get("id"))
    llm = get_llm(max_tokens=256)

    # ── Role & Backstory (from agents.yaml) ───────────────────────────────────
    backstory = (
        "You are the UrbanPulse Pipeline Monitor. Role: Final quality-check layer for Antalya Büyükşehir Belediyesi.\n"
        "Goal: Write a single concise sentence (max 120 chars) summarising the full AI pipeline decision.\n"
        "You must evaluate ALL prior context (classifier reasoning and planner action notes) to generate an accurate summary.\n"
        "IMPORTANT: Your summary output MUST be strictly in English."
    )

    # ── Task Instructions (from tasks.yaml) ───────────────────────────────────
    task_desc = (
        f"Write ONE sentence in English (max 120 chars) summarising the result for: {inc.get('title')}.\n"
        f"Example: 'P5 FIRE_HAZARD routed to Antalya İtfaiye Dairesi with 1h SLA due to critical forest risk.'\n"
        f"Use category ENUMs and priority codes like P5.\n"
        "Output ONLY the sentence — no quotes, no preamble."
    )

    hum_msg = (
        f"{task_desc}\n\n"
        f"--- RAW INCIDENT DATA ---\n"
        f"Title: {inc.get('title')}\n"
        f"Description: {inc.get('description')}\n"
        f"District: {inc.get('district')}\n\n"
        f"--- CLASSIFIER DECISION ---\n"
        f"Category: {state.get('category')}\n"
        f"Priority: P{state.get('priority')}\n"
        f"Confidence: {state.get('confidence')}\n"
        f"Reasoning: {state.get('reasoning')}\n"
        f"Override Reason: {state.get('override_reason', 'None')}\n\n"
        f"--- PLANNER DECISION ---\n"
        f"Department: {state.get('department')}\n"
        f"SLA: {state.get('sla_hours')}h\n"
        f"Action Note: {state.get('action_note')}\n"
    )

    res = llm.invoke([
        SystemMessage(content=backstory),
        HumanMessage(content=hum_msg)
    ])

    return {"summary": res.content.strip()[:200]}
