"""
urbanpulse.langgraph_pipeline.nodes.planner — Response planning node.

Assigns department and SLA based on classification results.
"""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from urbanpulse.core.config import get_settings
from urbanpulse.core.logging import get_logger
from urbanpulse.langgraph_pipeline.state import PipelineState
from urbanpulse.langgraph_pipeline.tools import LANGGRAPH_TOOLS
from urbanpulse.langgraph_pipeline.nodes.utils import invoke_with_tools, parse_llm_json

logger = get_logger(__name__)

def _get_llm() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.langgraph_model,
        api_key=s.openai_api_key,
        temperature=0,
        max_tokens=1024,
    )


def plan_node(state: PipelineState) -> dict:
    """Plan response using rich Antalya-specific instructions and tools."""
    inc = state["incident"]
    logger.info("node_start", node="planner", incident_id=inc.get("id"))
    cat = state.get("category", "OTHER")
    s = get_settings()
    llm = _get_llm()

    # ── Role & Backstory (from agents.yaml) ───────────────────────────────────
    backstory = (
        "You are an expert Antalya Büyükşehir Belediyesi Incident Response Planner. "
        "Goal: Assign the correct Antalya municipal department and a realistic SLA, detecting systemic patterns.\n"
        "Antalya context: You have 15 years experience routing incidents. You treat recurring incidents as systemic issues.\n"
        "Special Forest Rule: Districts like Kemer, Manavgat, Serik, Döşemealtı + FIRE/smoke → MUST be 'Antalya İtfaiye Dairesi' "
        "with minimum P5 and 0.25x SLA multiplier.\n"
        "Tourist Zone Rule: Muratpaşa, Alanya, Kemer, Serik, Kaş during May–October → 0.75x SLA multiplier for POWER_OUTAGE and FLOODING."
    )

    # ── Task Instructions (from tasks.yaml) ───────────────────────────────────
    task_desc = (
        "Plan the response. Call tools in order:\n"
        "1. check_similar_incidents   — ALWAYS (detect systemic patterns)\n"
        "2. get_district_risk_profile — for specialist department routing\n"
        "3. get_time_risk_context     — weekend/holiday adds 25% to SLA\n\n"
        "DEPARTMENTS & BASE SLAs:\n"
        "- Antalya Trafik Yönetim Müdürlüğü → TRAFFIC_ACCIDENT (4h)\n"
        "- Antalya Yollar ve Altyapı Dairesi → ROAD_DAMAGE (24h)\n"
        "- ASAT (Antalya Su ve Atıksu İdaresi) → FLOODING (8h)\n"
        "- AEDAŞ (Antalya Elektrik Dağıtım A.Ş.) → POWER_OUTAGE (6h)\n"
        "- Antalya İtfaiye Dairesi → FIRE_HAZARD (1h)\n"
        "- Antalya Zabıta ve Güvenlik Müdürlüğü → VANDALISM (48h)\n"
        "- Antalya Çevre Sağlığı Müdürlüğü → NOISE_COMPLAINT (72h)\n"
        "- Antalya Belediyesi Genel Hizmetler → OTHER (72h)\n\n"
        "SLA CALCULATION: base_sla × priority_mult × time_mult\n"
        "- priority_mult: P5=0.25x, P4=0.5x, P3=1x, P2=1.5x, P1=2x\n"
        "- time_mult: weekend/holiday = 1.25x\n"
        "Round up to nearest integer hour. If pattern_detected=true → include 'systemic issue' in action_note."
    )

    hum_msg = (
        f"{task_desc}\n\n"
        f"Incident Context:\n"
        f"- Title: {inc.get('title')}\n"
        f"- Description: {inc.get('description')}\n"
        f"- Category: {cat}\n"
        f"- Priority: P{state.get('priority')}\n"
        f"- District: {inc.get('district')}\n\n"
        "Output ONLY JSON: "
        '{"department": str, "sla_hours": int, "action_note": str}'
    )

    content = invoke_with_tools(
        llm=llm,
        messages=[SystemMessage(content=backstory), HumanMessage(content=hum_msg)],
        tools=LANGGRAPH_TOOLS,
        max_rounds=s.tool_max_rounds
    )
    
    data = parse_llm_json(content)

    return {
        "department":  data.get("department", "General Services"),
        "sla_hours":   int(data.get("sla_hours", 24)),
        "action_note": data.get("action_note", "Action planned with tools."),
    }
