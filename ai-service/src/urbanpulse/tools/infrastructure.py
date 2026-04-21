"""Overpass API — find nearby critical infrastructure. Free, no key, sync."""
from __future__ import annotations
import math, httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CATEGORY_MAP = {
    "hospital":"critical_medical","clinic":"critical_medical",
    "school":"educational","kindergarten":"educational",
    "fire_station":"emergency_services","police":"emergency_services",
    "fuel":"hazard_proximity","station":"transport","subway_entrance":"transport",
}


def _dist(lat1, lng1, lat2, lng2) -> int:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(lng2-lng1)/2)**2
    return int(R * 2 * math.asin(math.sqrt(a)))


def find_nearby_critical_infrastructure(latitude: float, longitude: float, radius_m: int = 500) -> dict:
    query = (
        f"[out:json][timeout:10];\n(\n"
        f'  node["amenity"~"hospital|clinic|school|kindergarten|fire_station|police|fuel"](around:{radius_m},{latitude},{longitude});\n'
        f'  node["railway"~"station|subway_entrance"](around:{radius_m},{latitude},{longitude});\n'
        f");\nout body;\n"
    )
    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(OVERPASS_URL, data={"data": query},
                               headers={"User-Agent": "UrbanPulse/3.0"})
            resp.raise_for_status()
            elements = resp.json().get("elements", [])

        cats: dict[str, list[str]] = {v: [] for v in set(CATEGORY_MAP.values())}
        for el in elements:
            tags    = el.get("tags", {})
            amenity = tags.get("amenity") or tags.get("railway", "")
            cat     = CATEGORY_MAP.get(amenity)
            if cat:
                name = tags.get("name") or amenity.replace("_", " ").title()
                d    = _dist(latitude, longitude, el["lat"], el["lon"])
                cats[cat].append(f"{name} ({d}m)")

        hospital_close = any(int(x.split("(")[-1].rstrip("m)")) < 300 for x in cats.get("critical_medical", []))
        fuel_close     = any(int(x.split("(")[-1].rstrip("m)")) < 100 for x in cats.get("hazard_proximity", []))
        auto_escalate  = hospital_close or fuel_close
        total          = sum(len(v) for v in cats.values())

        return {
            **cats,
            "total_found": total,
            "auto_escalate": auto_escalate,
            "escalation_reason": (
                "Hospital within 300m" if hospital_close
                else "Fuel station within 100m" if fuel_close else None
            ),
            "summary": f"{total} critical facilities nearby." + (" AUTO-ESCALATE." if auto_escalate else ""),
        }
    except httpx.TimeoutException:
        return {"total_found": 0, "auto_escalate": False, "summary": "Infrastructure data unavailable (timeout)"}
    except Exception as exc:
        return {"total_found": 0, "auto_escalate": False, "summary": f"Infrastructure data unavailable: {exc}"}
