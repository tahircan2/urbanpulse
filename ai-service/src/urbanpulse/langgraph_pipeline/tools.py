"""
urbanpulse.langgraph_pipeline.tools — LangChain @tool wrappers (Dual Mode).

This module operates in two modes:
    1. DIRECT MODE (default fallback):
       Tools are imported directly from urbanpulse.tools.* and wrapped
       with @tool decorators. This is the original approach — fast and simple.

    2. MCP MODE (when MCP client is connected):
       Tools are dynamically discovered from the MCP Server via the
       Model Context Protocol. Each tool call goes through:
       LangGraph → MCP Client → stdio → MCP Server → urbanpulse.tools.*

The active mode is determined at runtime by checking the MCP client
connection state. This dual-mode approach allows:
    - Graceful fallback if MCP server is unavailable
    - Side-by-side comparison for demonstration purposes
    - Zero downtime during MCP integration
"""
import json
from langchain_core.tools import tool

from urbanpulse.core.logging import get_logger

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# DIRECT MODE TOOLS (Original — framework-native LangChain wrappers)
# ══════════════════════════════════════════════════════════════════════════════

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


# ── Direct Mode Tool List ─────────────────────────────────────────────────────
DIRECT_TOOLS = [
    weather_context_tool,
    district_risk_tool,
    time_context_tool,
    infrastructure_tool,
    geolocation_tool,
    similar_incidents_tool,
]


# ══════════════════════════════════════════════════════════════════════════════
# DUAL MODE RESOLVER
# ══════════════════════════════════════════════════════════════════════════════

def get_active_tools(prefer_mcp: bool = True) -> tuple[list, str]:
    """
    Resolve the active tool list based on MCP connection state.

    Args:
        prefer_mcp: If True, use MCP tools when available. If False, always use direct.

    Returns:
        Tuple of (tool_list, mode_label) where mode_label is 'mcp' or 'direct'.
    """
    if prefer_mcp:
        try:
            from urbanpulse.mcp_client.manager import get_mcp_manager
            manager = get_mcp_manager()

            if manager.is_connected:
                from urbanpulse.mcp_client.adapter import build_mcp_langchain_tools
                mcp_tools = build_mcp_langchain_tools()

                if mcp_tools:
                    logger.info(
                        "tools_mode_resolved",
                        mode="mcp",
                        count=len(mcp_tools),
                        tools=[t.name for t in mcp_tools],
                    )
                    return mcp_tools, "mcp"

                logger.warning("mcp_tools_empty_fallback_to_direct")

        except ImportError:
            logger.debug("mcp_package_not_available_using_direct")
        except Exception as exc:
            logger.warning("mcp_tools_error_fallback", error=str(exc))

    logger.info(
        "tools_mode_resolved",
        mode="direct",
        count=len(DIRECT_TOOLS),
    )
    return DIRECT_TOOLS, "direct"


# ── Legacy Compatibility ──────────────────────────────────────────────────────
# LANGGRAPH_TOOLS is kept for backward compatibility with existing node imports
LANGGRAPH_TOOLS = DIRECT_TOOLS
