"""Query Spring Boot backend for incident pattern detection. Sync."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import httpx
from urbanpulse.core.config import get_settings


def check_similar_incidents(district: str, category: str, days_back: int = 7) -> dict:
    settings = get_settings()
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(
                f"{settings.spring_backend_url.rstrip('/')}/incidents",
                params={"district": district, "category": category, "size": 50},
                headers={"X-Internal-Secret": settings.internal_secret},
            )
            resp.raise_for_status()
            data = resp.json()

        content = data.get("data", {}).get("content", []) if data.get("success") else []
        cutoff  = datetime.now(timezone.utc) - timedelta(days=days_back)
        recent  = [
            inc for inc in content
            if inc.get("status") in ("PENDING", "IN_PROGRESS")
            and datetime.fromisoformat(inc["createdAt"].replace("Z", "+00:00")) > cutoff
        ]
        pattern = len(recent) >= 3

        return {
            "similar_count": len(recent),
            "pattern_detected": pattern,
            "recommendation": (
                "Infrastructure review required — systemic issue detected."
                if pattern else "Isolated incident — standard response."
            ),
            "summary": (
                f"{district}: {len(recent)} similar {category} incidents in {days_back} days. "
                + ("PATTERN DETECTED." if pattern else "No pattern.")
            ),
        }
    except Exception as exc:
        return {"similar_count": 0, "pattern_detected": False,
                "summary": "Pattern data unavailable.", "recommendation": "Treat as isolated."}
