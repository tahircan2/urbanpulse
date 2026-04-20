"""
urbanpulse.langgraph_pipeline.nodes.planner — Response planning node.

Assigns department and SLA based on classification results.
"""
from __future__ import annotations

import json

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
        max_tokens=1024,
    )


def _parse_json(content: str) -> dict:
    """Extract JSON from LLM output."""
    try:
        clean = content.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)
    except Exception:
        s, e = content.find("{"), content.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(content[s:e])
            except Exception:
                pass
        return {}


def plan_node(state: PipelineState) -> dict:
    """Plan response: assign department and calculate SLA."""
    inc = state["incident"]
    cat = state.get("category", "OTHER")
    llm = _get_llm()

    sys_msg = "You are Planner. Output JSON ONLY."
    hum_msg = (
        f"Plan response for incident.\n"
        f"Title: {inc.get('title')}\n"
        f"Category: {cat}\n"
        f"Priority: {state.get('priority')}\n"
        f'Output JSON format: {{"department": str, "sla_hours": int, "action_note": str}}'
    )

    res = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=hum_msg)])
    data = _parse_json(res.content)

    return {
        "department":  data.get("department", "General Services"),
        "sla_hours":   int(data.get("sla_hours", 24)),
        "action_note": data.get("action_note", "Action planned."),
    }
