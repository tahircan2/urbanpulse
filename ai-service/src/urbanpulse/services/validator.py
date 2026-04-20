"""
urbanpulse.services.validator — Rule-based content consistency checker.

No LLM calls; the Classifier agent handles semantic analysis.
This module catches obvious category/content mismatches and produces warnings.
"""
from __future__ import annotations

from urbanpulse.models.enums import IncidentCategory
from urbanpulse.models.incident import IncidentDTO

# ── Category keyword map ─────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[IncidentCategory, list[str]] = {
    IncidentCategory.TRAFFIC_ACCIDENT: [
        "kaza", "çarpışma", "trafik", "araç", "motorlu", "otobüs", "taksi",
        "accident", "collision", "crash", "vehicle",
    ],
    IncidentCategory.ROAD_DAMAGE: [
        "çukur", "asfalt", "yol bozuk", "kaldırım", "delik", "çatlak",
        "pothole", "road damage", "cracked", "pavement",
    ],
    IncidentCategory.FLOODING: [
        "sel", "su baskını", "taşkın", "yağmur", "dere", "göl",
        "flood", "flooding", "overflow", "waterlogging",
    ],
    IncidentCategory.POWER_OUTAGE: [
        "elektrik", "kesinti", "karanlık", "sigorta", "trafo",
        "power", "electricity", "outage", "blackout",
    ],
    IncidentCategory.FIRE_HAZARD: [
        "yangın", "yanıyor", "alev", "duman", "patlama", "gaz sızıntısı",
        "fire", "burning", "smoke", "explosion", "gas leak",
    ],
    IncidentCategory.VANDALISM: [
        "kırık", "vandal", "hasar", "tahrip", "grafiti",
        "vandalism", "graffiti", "broken", "damaged", "destroyed",
    ],
    IncidentCategory.NOISE_COMPLAINT: [
        "gürültü", "ses", "şikâyet", "rahatsızlık", "müzik", "bağırma",
        "noise", "loud", "complaint", "disturbance",
    ],
}

_NO_MATCH_WARNING = "İçerik seçilen kategoriye uymayabilir; Classifier doğrulayacak."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _combined_text(incident: IncidentDTO) -> str:
    """Combine title + description in lowercase for keyword matching."""
    return f"{incident.title} {incident.description}".lower()


def _keywords_for(category: IncidentCategory) -> list[str]:
    """Return keyword list for a category."""
    return _CATEGORY_KEYWORDS.get(category, [])


def _find_suggested_category(text: str) -> IncidentCategory | None:
    """Find the best-matching category based on keyword hits."""
    best: tuple[IncidentCategory, int] | None = None
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > 0 and (best is None or hits > best[1]):
            best = (cat, hits)
    return best[0] if best else None


# ── Public API ────────────────────────────────────────────────────────────────

def check_content_consistency(incident: IncidentDTO) -> dict:
    """
    Check consistency between title/description and category.

    Returns:
        {"consistent": bool, "warning": str, "suggested_category": str | None}
    """
    text = _combined_text(incident)
    keywords = _keywords_for(incident.category)

    category_hit = any(kw in text for kw in keywords)
    if category_hit:
        return {"consistent": True, "warning": "", "suggested_category": None}

    suggested = _find_suggested_category(text)
    warning = (
        f"Kullanıcı '{incident.category.value}' seçti ama içerik "
        f"'{suggested.value if suggested else 'OTHER'}' ile daha uyumlu görünüyor."
        if suggested and suggested != incident.category
        else _NO_MATCH_WARNING
    )

    return {
        "consistent": False,
        "warning": warning,
        "suggested_category": suggested.value if suggested else None,
    }
