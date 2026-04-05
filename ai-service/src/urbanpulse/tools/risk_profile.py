"""
tools/risk_profile.py — Static Antalya district risk profiles. No I/O, instant.

Antalya'nın 13 ilçesi için risk profili veritabanı.
Temel riskler: orman yangını, sahil/turizm yoğunluğu, sel, altyapı yaşı.
"""
from __future__ import annotations

PROFILES: dict[str, dict] = {
    "Muratpaşa": {
        "flood_risk": "medium",
        "traffic_density": "very_high",
        "tourism_zone": True,
        "infrastructure_age": "old",
        "population_density": "very_high",
        "historic_area": True,
        "commercial_density": "high",
    },
    "Kepez": {
        "flood_risk": "medium",
        "population_density": "very_high",
        "industrial_zone": True,
        "traffic_density": "high",
    },
    "Konyaaltı": {
        "flood_risk": "high",
        "coastal": True,
        "tourism_zone": True,
        "traffic_density": "high",
        "population_density": "high",
    },
    "Alanya": {
        "flood_risk": "medium",
        "coastal": True,
        "tourism_zone": True,
        "forest_risk": "medium",
        "seasonal_population": "very_high",
        "traffic_density": "high",
    },
    "Manavgat": {
        "flood_risk": "medium",
        "forest_risk": "very_high",
        "coastal": True,
        "tourism_zone": True,
        "river_proximity": True,
    },
    "Serik": {
        "flood_risk": "low",
        "forest_risk": "high",
        "coastal": True,
        "tourism_zone": True,   # Belek turizm bölgesi
    },
    "Döşemealtı": {
        "flood_risk": "high",
        "forest_risk": "high",
        "mountain_terrain": True,
        "rural": True,
        "infrastructure_age": "old",
    },
    "Aksu": {
        "flood_risk": "low",
        "airport_proximity": True,
        "industrial_zone": True,
        "traffic_density": "medium",
    },
    "Kemer": {
        "flood_risk": "medium",
        "coastal": True,
        "forest_risk": "very_high",
        "tourism_zone": True,
        "mountain_terrain": True,
        "seasonal_population": "high",
    },
    "Kumluca": {
        "flood_risk": "low",
        "coastal": True,
        "forest_risk": "high",
        "agricultural_zone": True,
        "rural": True,
    },
    "Kaş": {
        "flood_risk": "low",
        "coastal": True,
        "mountain_terrain": True,
        "tourism_zone": True,
        "forest_risk": "medium",
        "seasonal_population": "high",
    },
    "Finike": {
        "flood_risk": "medium",
        "coastal": True,
        "agricultural_zone": True,
        "river_proximity": True,
    },
    "Demre": {
        "flood_risk": "low",
        "coastal": True,
        "tourism_zone": True,   # Myra antik kenti
        "agricultural_zone": True,
    },
}

_DEFAULT = {"flood_risk": "medium", "traffic_density": "medium", "tourism_zone": False}


def get_district_risk_profile(district: str) -> dict:
    profile = PROFILES.get(district)
    if not profile:
        dl = district.lower()
        for k, v in PROFILES.items():
            if k.lower() in dl or dl in k.lower():
                profile = v
                break
    profile = profile or _DEFAULT

    risks = []
    flood = profile.get("flood_risk", "medium")
    if flood in ("high", "very_high"):
        risks.append(f"flood risk: {flood}")
    if profile.get("forest_risk") in ("high", "very_high"):
        risks.append(f"⚠️ FOREST FIRE RISK: {profile['forest_risk']}")
    if profile.get("infrastructure_age") in ("old", "very_old"):
        risks.append(f"aging infrastructure ({profile['infrastructure_age']})")
    if profile.get("historic_area"):
        risks.append("historic area — restricted access")
    if profile.get("industrial_zone"):
        risks.append("industrial zone")
    if profile.get("coastal"):
        risks.append("Mediterranean coastline")
    if profile.get("mountain_terrain"):
        risks.append("mountain terrain — difficult access")
    if profile.get("tourism_zone"):
        risks.append("tourism zone — high seasonal population")
    if profile.get("river_proximity"):
        risks.append("river proximity — flash flood risk")
    if profile.get("airport_proximity"):
        risks.append("airport proximity — restricted airspace operations")
    if profile.get("seasonal_population") in ("high", "very_high"):
        risks.append(f"seasonal population surge ({profile['seasonal_population']})")

    return {
        **profile,
        "district": district,
        "risk_summary": ", ".join(risks) or "Normal risk profile",
    }
