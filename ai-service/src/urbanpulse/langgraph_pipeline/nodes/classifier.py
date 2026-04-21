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
from urbanpulse.core.logging import get_logger
from urbanpulse.langgraph_pipeline.state import PipelineState
from urbanpulse.langgraph_pipeline.tools import LANGGRAPH_TOOLS
from urbanpulse.langgraph_pipeline.nodes.utils import invoke_with_tools, parse_llm_json, get_llm

logger = get_logger(__name__)

def classify_node(state: PipelineState) -> dict:
    """Classify the incident using rich Antalya-specific instructions and tools."""
    inc = state["incident"]
    logger.info("node_start", node="classifier", incident_id=inc.get("id"))
    s = get_settings()
    llm = get_llm(max_tokens=1024)

    # ── Role & Backstory (from agents.yaml) ───────────────────────────────────
    backstory = (
        "You are an expert Antalya Smart City Incident Classifier. "
        "Goal: Accurately classify the category and priority of Antalya city incidents, "
        "overriding user-reported values when the description implies different severity.\n"
        "Antalya's unique risks include: intense summer forest fire risk in districts like Kemer, "
        "Manavgat and Döşemealtı; flash flooding in Konyaaltı and Döşemealtı during autumn rains; "
        "critical infrastructure stress during peak tourist season (May–October) in Muratpaşa, Alanya and Serik (Belek).\n"
        "CRITICAL: Never blindly trust the user's category. A mislabelled P1 forest fire reported as P3 could cost lives. "
        "If they describe a gas leak but chose NOISE_COMPLAINT, you MUST correct it and set 'override_reason'."
    )

    # ── Task Instructions (from tasks.yaml) ───────────────────────────────────
    task_desc = (
        "Classify this Antalya incident. CALL TOOLS IN ORDER:\n"
        "1. get_district_risk_profile  — ALWAYS first\n"
        "2. get_time_risk_context      — ALWAYS (rush hour/tourist season affects priority)\n"
        "3. get_weather_context        — for FLOODING, FIRE_HAZARD, ROAD_DAMAGE, POWER_OUTAGE, TRAFFIC_ACCIDENT\n"
        "4. find_nearby_critical_infrastructure — if initial priority >= 3\n"
        "5. get_location_context       — only if reported district seems wrong for coordinates\n\n"
        "ADJUSTMENT RULES:\n"
        "- Life-threatening text in description → P5\n"
        "- Heavy rain + FLOODING → +2 priority\n"
        "- Forest-risk district (Kemer, Manavgat, Serik, Döşemealtı) + FIRE_HAZARD/smoke → minimum P5\n"
        "- Rush hour + TRAFFIC_ACCIDENT → +1\n"
        "- tourist_zone=true + Tourist season (May–Oct) → +1 (infrastructure stress)\n"
        "IMPORTANT: Your 'reasoning' MUST be a clear, user-friendly English sentence explaining why this priority/category was chosen. Do not use system logs or variable names in the text."
    )

    hum_msg = (
        f"{task_desc}\n\n"
        f"Incident Data:\n"
        f"- Title: {inc.get('title')}\n"
        f"- Description: {inc.get('description')}\n"
        f"- Category (User): {inc.get('category')}\n"
        f"- Priority (User): P{inc.get('priority')}\n"
        f"- District: {inc.get('district')}\n"
        f"- Coords: {inc.get('latitude')}, {inc.get('longitude')}\n"
        f"- Consistency: {state.get('consistency_warning')}\n\n"
        "Output ONLY JSON: "
        '{"category": str, "priority": int, "confidence": float, "reasoning": str, "override_reason": str}'
    )

    content = invoke_with_tools(
        llm=llm,
        messages=[SystemMessage(content=backstory), HumanMessage(content=hum_msg)],
        tools=LANGGRAPH_TOOLS,
        max_rounds=s.tool_max_rounds
    )
    
    data = parse_llm_json(content)

    return {
        "category":        data.get("category", inc.get("category", "OTHER")),
        "priority":        data.get("priority", inc.get("priority", 3)),
        "confidence":      data.get("confidence", 0.75),
        "reasoning":       data.get("reasoning", "Classified with tools."),
        "override_reason": data.get("override_reason", ""),
    }
