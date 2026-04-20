"""
urbanpulse.langgraph_pipeline.tools — LangChain @tool wrappers.

These tools reuse the core logic from urbanpulse/tools/ while adhering
to standard LangChain functional tool patterns.
"""
import json
from langchain_core.tools import tool


@tool
def weather_context_tool(latitude: float, longitude: float) -> str:
    """
    Current weather at incident coordinates (Open-Meteo).
    Call for FLOODING, FIRE_HAZARD, ROAD_DAMAGE, POWER_OUTAGE, TRAFFIC_ACCIDENT.
    Returns precipitation, wind, temperature and priority_boost.
    """
    from urbanpulse.tools.weather import get_weather_context
    return json.dumps(get_weather_context(latitude, longitude))


@tool
def district_risk_tool(district: str) -> str:
    """
    Antalya district risk profile: flood risk, industrial zone, chemical hazard.
    Always call this first for any incident to get local context.
    """
    from urbanpulse.tools.risk_profile import get_district_risk_profile
    return json.dumps(get_district_risk_profile(district))


@tool
def time_context_tool() -> str:
    """
    Current time context: rush hour, school hours, night, public holiday.
    Always call this — affects priority scoring and SLA.
    """
    from urbanpulse.tools.time_context import get_time_risk_context
    return json.dumps(get_time_risk_context())


@tool
def infrastructure_tool(latitude: float, longitude: float, radius_m: int = 500) -> str:
    """
    Find hospitals, schools, fire stations near incident via Overpass/OSM.
    Call for priority >= 3.
    """
    from urbanpulse.tools.infrastructure import find_nearby_critical_infrastructure
    return json.dumps(find_nearby_critical_infrastructure(latitude, longitude, radius_m))


@tool
def geolocation_tool(latitude: float, longitude: float) -> str:
    """
    Reverse-geocode coordinates to street/neighbourhood (Nominatim).
    Call only if reported district seems inconsistent with coordinates.
    """
    from urbanpulse.tools.geocoding import get_location_context
    return json.dumps(get_location_context(latitude, longitude))


@tool
def similar_incidents_tool(district: str, category: str, days_back: int = 7) -> str:
    """
    Check for similar open incidents in the same district and category.
    Essential for detecting systemic issues.
    """
    from urbanpulse.tools.patterns import check_similar_incidents
    return json.dumps(check_similar_incidents(district, category, days_back))


# ── Tool List ─────────────────────────────────────────────────────────────────
LANGGRAPH_TOOLS = [
    weather_context_tool,
    district_risk_tool,
    time_context_tool,
    infrastructure_tool,
    geolocation_tool,
    similar_incidents_tool,
]
