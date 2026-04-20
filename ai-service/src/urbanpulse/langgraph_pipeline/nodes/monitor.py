"""
urbanpulse.langgraph_pipeline.nodes.monitor — Pipeline summary node.

Produces a concise one-line summary of the pipeline result.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from urbanpulse.core.config import get_settings
from urbanpulse.langgraph_pipeline.state import PipelineState


def _get_llm() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.langgraph_model,
        api_key=s.openai_api_key,
        temperature=0,
        max_tokens=256,
    )


def monitor_node(state: PipelineState) -> dict:
    """Summarise the pipeline result in a single concise English sentence."""
    inc = state["incident"]
    llm = _get_llm()

    # ── Role & Backstory (from agents.yaml) ───────────────────────────────────
    backstory = (
        "You are the UrbanPulse Pipeline Monitor. Role: Final quality-check layer for Antalya Büyükşehir Belediyesi.\n"
        "Goal: Write a single concise sentence (max 120 chars) summarising the full AI pipeline decision.\n"
        "IMPORTANT: Your summary output MUST be strictly in English."
    )

    # ── Task Instructions (from tasks.yaml) ───────────────────────────────────
    task_desc = (
        f"Write ONE sentence in English (max 120 chars) summarising the result for: {inc.get('title')}.\n"
        f"Example: 'P5 FIRE_HAZARD routed to Antalya İtfaiye Dairesi with 1h SLA.'\n"
        f"Use category ENUMs and priority codes like P5.\n"
        "Output ONLY the sentence — no quotes, no preamble."
    )

    res = llm.invoke([
        SystemMessage(content=backstory),
        HumanMessage(content=f"{task_desc}\n\nContext:\n- Category: {state.get('category')}\n- Priority: {state.get('priority')}\n- Dept: {state.get('department')}\n- SLA: {state.get('sla_hours')}h")
    ])

    return {"summary": res.content.strip()[:200]}
