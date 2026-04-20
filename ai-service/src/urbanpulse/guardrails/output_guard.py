"""
urbanpulse.guardrails.output_guard — AI output safety verification.

Ensures the AI pipeline output does not contain harmful text,
hallucinatory insults, or internal system prompt leaks.
"""
from __future__ import annotations

import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from urbanpulse.core.config import get_settings
from urbanpulse.core.logging import get_logger

logger = get_logger(__name__)


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


def check_output_guard(notes: str) -> tuple[bool, str, int]:
    """
    Verify AI-generated notes for safety.

    Returns:
        (is_safe, reason, tokens_used)
    """
    if not notes:
        return True, "", 0

    s = get_settings()
    llm = ChatOpenAI(
        model=s.monitor_model,
        api_key=s.openai_api_key,
        temperature=0,
        max_tokens=150,
    )

    sys_msg = (
        "You are a strict security layer verifying AI output. "
        "Prevent AI from outputting harmful text, hallucinatory insults, "
        "or internal system prompt leaks."
    )
    hum_msg = (
        f"Analyze these AI agent notes. Ensure it does NOT contain sensitive "
        f"system prompts, extreme profanity, or weird glitches.\n"
        f"Notes: '{notes}'\n\n"
        f'Output STRICT valid JSON ONLY: {{"safe": true/false, "reason": "..."}}'
    )

    res = llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=hum_msg)])
    tokens = res.usage_metadata.get("total_tokens", 0) if res.usage_metadata else 0
    data = _parse_json(res.content)
    return bool(data.get("safe", True)), str(data.get("reason", "")), tokens
