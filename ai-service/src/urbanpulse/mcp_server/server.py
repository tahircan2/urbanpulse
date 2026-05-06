"""
urbanpulse.mcp_server.server — UrbanPulse MCP Server (FastMCP).

A standards-compliant Model Context Protocol server that exposes
UrbanPulse's six core city-intelligence tools over stdio transport.

Protocol: JSON-RPC 2.0 over stdio
SDK:      mcp (official Anthropic Python SDK)
Pattern:  FastMCP decorator-based tool registration

Tools exposed:
    1. weather_context        — Real-time weather from Open-Meteo
    2. district_risk_profile  — Static Antalya district risk data
    3. time_risk_context      — Time-based risk factors (rush hour, holidays)
    4. nearby_infrastructure  — Critical infrastructure via Overpass/OSM
    5. reverse_geocode        — Reverse geocoding via Nominatim
    6. similar_incidents      — Pattern detection from Spring Boot backend

Resources exposed:
    - urbanpulse://districts  — List of all Antalya districts with risk profiles
    - urbanpulse://server-info — MCP server metadata and capabilities

Usage:
    python -m urbanpulse.mcp_server.server          # stdio transport
    mcp dev src/urbanpulse/mcp_server/server.py      # MCP Inspector (dev)
"""
from __future__ import annotations

import json
import sys
import logging

from mcp.server.fastmcp import FastMCP

# ── Logging Configuration ─────────────────────────────────────────────────────
# CRITICAL: stdio transport uses stdout for JSON-RPC messages.
# ALL logging MUST go to stderr to avoid corrupting the protocol stream.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP-SERVER] %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("urbanpulse.mcp_server")

# ── FastMCP Server Instance ───────────────────────────────────────────────────
mcp = FastMCP(
    "urbanpulse-tools",
    instructions=(
        "UrbanPulse Smart City Incident Management Tools. "
        "These tools provide real-time contextual data for Antalya, Turkey — "
        "including weather, district risk profiles, time-based risk factors, "
        "nearby critical infrastructure, geocoding, and incident pattern detection. "
        "Use these tools to enrich incident classification and response planning."
    ),
)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 1: Weather Context
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def weather_context(latitude: float, longitude: float) -> str:
    """
    Get current weather conditions at incident coordinates via Open-Meteo API.

    Returns temperature, precipitation, wind speed, humidity, visibility,
    flood risk assessment, fire weather conditions, and priority boost
    recommendation based on weather severity.

    Use for: FLOODING, FIRE_HAZARD, ROAD_DAMAGE, POWER_OUTAGE, TRAFFIC_ACCIDENT incidents.

    Args:
        latitude: Latitude coordinate of the incident location (e.g., 36.8841)
        longitude: Longitude coordinate of the incident location (e.g., 30.7056)
    """
    logger.info("Tool called: weather_context(lat=%s, lng=%s)", latitude, longitude)
    from urbanpulse.tools.weather import get_weather_context
    result = get_weather_context(latitude, longitude)
    logger.info("Tool result: weather_context → %s", result.get("summary", "N/A"))
    return json.dumps(result, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 2: District Risk Profile
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def district_risk_profile(district: str) -> str:
    """
    Get the static risk profile for an Antalya district.

    Returns flood risk level, forest fire risk, infrastructure age,
    tourism zone status, traffic density, coastal proximity, and
    a composite risk summary. Covers all 13 Antalya districts.

    ALWAYS call this tool first for any incident to establish local context.

    Args:
        district: Name of the Antalya district (e.g., "Kemer", "Muratpaşa", "Döşemealtı")
    """
    logger.info("Tool called: district_risk_profile(district=%s)", district)
    from urbanpulse.tools.risk_profile import get_district_risk_profile
    result = get_district_risk_profile(district)
    logger.info("Tool result: district_risk_profile → %s", result.get("risk_summary", "N/A"))
    return json.dumps(result, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 3: Time Risk Context
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def time_risk_context() -> str:
    """
    Get current time-based risk context for Antalya (Europe/Istanbul timezone).

    Returns rush hour status, school hours, night time, weekend/holiday
    indicators, SLA modifier recommendations, and priority adjustment notes.
    Includes Turkish public holiday calendar awareness.

    ALWAYS call this tool — time context affects priority scoring and SLA calculation.
    """
    logger.info("Tool called: time_risk_context()")
    from urbanpulse.tools.time_context import get_time_risk_context
    result = get_time_risk_context()
    logger.info("Tool result: time_risk_context → %s", result.get("summary", "N/A"))
    return json.dumps(result, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 4: Nearby Critical Infrastructure
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def nearby_infrastructure(latitude: float, longitude: float, radius_m: int = 500) -> str:
    """
    Find nearby critical infrastructure (hospitals, schools, fire stations,
    police stations, fuel stations, transit) using OpenStreetMap Overpass API.

    Returns categorized facilities with distances, total count, and
    auto-escalation recommendation if hospitals (<300m) or fuel stations
    (<100m) are within proximity.

    Call for incidents with priority >= 3.

    Args:
        latitude: Latitude coordinate of the incident location
        longitude: Longitude coordinate of the incident location
        radius_m: Search radius in meters (default: 500, max recommended: 1000)
    """
    logger.info("Tool called: nearby_infrastructure(lat=%s, lng=%s, radius=%d)", latitude, longitude, radius_m)
    from urbanpulse.tools.infrastructure import find_nearby_critical_infrastructure
    result = find_nearby_critical_infrastructure(latitude, longitude, radius_m)
    logger.info("Tool result: nearby_infrastructure → %s", result.get("summary", "N/A"))
    return json.dumps(result, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 5: Reverse Geocode
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def reverse_geocode(latitude: float, longitude: float) -> str:
    """
    Reverse-geocode coordinates to street address and neighbourhood
    using OpenStreetMap Nominatim API.

    Returns road name, neighbourhood, district, and full display name
    in Turkish locale. Rate limited to 1 request/second per Nominatim policy.

    Call only if the reported district seems inconsistent with coordinates.

    Args:
        latitude: Latitude coordinate to geocode
        longitude: Longitude coordinate to geocode
    """
    logger.info("Tool called: reverse_geocode(lat=%s, lng=%s)", latitude, longitude)
    from urbanpulse.tools.geocoding import get_location_context
    result = get_location_context(latitude, longitude)
    logger.info("Tool result: reverse_geocode → %s", result.get("summary", "N/A"))
    return json.dumps(result, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 6: Similar Incidents (Pattern Detection)
# ══════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def similar_incidents(district: str, category: str, days_back: int = 7) -> str:
    """
    Check for similar open/in-progress incidents in the same district
    and category from the Spring Boot backend database.

    Detects systemic patterns when 3+ similar incidents exist within
    the lookback window. Essential for identifying recurring infrastructure
    failures vs isolated incidents.

    Args:
        district: District name to search incidents in (e.g., "Konyaaltı")
        category: Incident category to match (e.g., "FLOODING", "POWER_OUTAGE")
        days_back: Number of days to look back for pattern detection (default: 7)
    """
    logger.info("Tool called: similar_incidents(district=%s, category=%s, days=%d)", district, category, days_back)
    from urbanpulse.tools.patterns import check_similar_incidents
    result = check_similar_incidents(district, category, days_back)
    logger.info("Tool result: similar_incidents → %s", result.get("summary", "N/A"))
    return json.dumps(result, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# RESOURCE: District Registry
# ══════════════════════════════════════════════════════════════════════════════
@mcp.resource("urbanpulse://districts")
def get_districts_registry() -> str:
    """Complete list of Antalya districts with their risk profiles."""
    from urbanpulse.tools.risk_profile import PROFILES
    return json.dumps(
        {district: profile for district, profile in PROFILES.items()},
        ensure_ascii=False,
        indent=2,
    )


@mcp.resource("urbanpulse://server-info")
def get_server_info() -> str:
    """MCP server metadata, version, and capability summary."""
    return json.dumps({
        "name": "urbanpulse-tools",
        "version": "3.0.0",
        "protocol": "Model Context Protocol (MCP)",
        "transport": "stdio",
        "sdk": "mcp (official Anthropic Python SDK)",
        "tools_count": 6,
        "resources_count": 2,
        "tools": [
            "weather_context",
            "district_risk_profile",
            "time_risk_context",
            "nearby_infrastructure",
            "reverse_geocode",
            "similar_incidents",
        ],
        "description": "UrbanPulse Smart City Incident Management — Antalya, Turkey",
    }, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# Server Entry Point
# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    """Launch the MCP server with stdio transport."""
    logger.info("UrbanPulse MCP Server v3.0.0 starting (transport=stdio)")
    logger.info("Registered 6 tools, 2 resources")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
