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
    """Summarise the pipeline result in a single sentence."""
    inc = state["incident"]
    llm = _get_llm()

    hum_msg = (
        f"Summarize short pipeline action for: {inc.get('title')}. "
        f"Dept: {state.get('department')}, SLA: {state.get('sla_hours')}"
    )

    res = llm.invoke([
        SystemMessage(content=(
            "You are the Communications Monitor for the city. Write a formal, professional, and corporate "
            "one-sentence summary in English stating that 'the relevant incident has been examined and forwarded to the relevant department for resolution'. "
            "Do not include robotic outputs. Keep it polite, brief, and professional."
        )),
        HumanMessage(content=hum_msg),
    ])

    return {"summary": res.content.strip()[:200]}
