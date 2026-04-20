"""
urbanpulse.langgraph_pipeline.nodes.classifier — Incident classification node.

Analyses incident text to determine category, priority, confidence,
and reasoning. Optionally uses tools for contextual enrichment.
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
    """Extract JSON from LLM output, stripping markdown fences."""
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


def classify_node(state: PipelineState) -> dict:
    """Classify the incident and return category/priority/confidence."""
    inc = state["incident"]
    llm = _get_llm()

    sys_msg = (
        "You are an expert Incident Classifier. Output JSON at the end: "
        '{"category": str, "priority": int, "confidence": float, '
        '"reasoning": str, "override_reason": str}\n'
        "VALID CATEGORIES: TRAFFIC_ACCIDENT, ROAD_DAMAGE, FLOODING, POWER_OUTAGE, FIRE_HAZARD, VANDALISM, NOISE_COMPLAINT, OTHER.\n"
        "CRITICAL: Do NOT blindly trust the user's category. If their description "
        "(e.g., 'cat stuck in tree') contradicts their chosen category (e.g., 'Traffic Accident'), "
        "you MUST correct the category to the structurally appropriate one from the VALID CATEGORIES list and set "
        "'override_reason' explaining why you changed it. If no category fits, use OTHER."
    )
    hum_msg = (
        f"Classify this incident.\n"
        f"Title: {inc.get('title')}\n"
        f"Desc: {inc.get('description')}\n"
        f"Dist: {inc.get('district')}\n"
        f"Coords: {inc.get('latitude')}, {inc.get('longitude')}\n"
        f"Call tools if needed, then output JSON with category, priority, "
        f"confidence, reasoning, override_reason."
    )

    res = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=hum_msg)])
    data = _parse_json(res.content)

    return {
        "category":        data.get("category", inc.get("category", "OTHER")),
        "priority":        data.get("priority", inc.get("priority", 3)),
        "confidence":      data.get("confidence", 0.75),
        "reasoning":       data.get("reasoning", "Classified."),
        "override_reason": data.get("override_reason", ""),
    }
