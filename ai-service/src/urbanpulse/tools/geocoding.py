"""Nominatim reverse geocoding — free, no key, sync. Rate limit: 1 req/sec."""
from __future__ import annotations
import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS       = {"User-Agent": "UrbanPulse/3.0 (Istanbul smart-city)"}


def get_location_context(latitude: float, longitude: float) -> dict:
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(NOMINATIM_URL, params={
                "lat": latitude, "lon": longitude,
                "format": "json", "addressdetails": 1, "accept-language": "tr",
            }, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()

        addr = data.get("address", {})
        road = addr.get("road", "")
        nbhd = addr.get("neighbourhood") or addr.get("suburb", "")
        dist = addr.get("district") or addr.get("county", "")
        return {
            "road": road, "neighbourhood": nbhd, "district": dist,
            "display_name": data.get("display_name", ""),
            "summary": f"{road}, {nbhd} ({dist})".strip(", "),
        }
    except httpx.TimeoutException:
        return {"error": "timeout", "summary": "Location unavailable"}
    except Exception as exc:
        return {"error": str(exc), "summary": "Location unavailable"}
