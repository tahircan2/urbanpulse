"""
CrewAI BaseTool wrappers.
Each class exposes one sync function to CrewAI agents via a typed input schema.
The LLM reads `description` to decide when to call each tool.
"""
from __future__ import annotations
import json
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from urbanpulse.tools.weather        import get_weather_context
from urbanpulse.tools.risk_profile   import get_district_risk_profile
from urbanpulse.tools.time_context   import get_time_risk_context
from urbanpulse.tools.infrastructure import find_nearby_critical_infrastructure
from urbanpulse.tools.geocoding      import get_location_context
from urbanpulse.tools.patterns       import check_similar_incidents


# ── Input Schemas ─────────────────────────────────────────────────────────────

class CoordInput(BaseModel):
    latitude:  float = Field(description="Incident latitude")
    longitude: float = Field(description="Incident longitude")

class CoordRadiusInput(BaseModel):
    latitude:  float = Field(description="Incident latitude")
    longitude: float = Field(description="Incident longitude")
    radius_m:  int   = Field(default=500, description="Search radius in metres")

class DistrictInput(BaseModel):
    district: str = Field(description="Istanbul district name in Turkish")

class SimilarInput(BaseModel):
    district:  str = Field(description="Istanbul district name")
    category:  str = Field(description="Incident category enum value")
    days_back: int = Field(default=7, description="Days to look back")

class EmptyInput(BaseModel):
    pass


# ── Tools ─────────────────────────────────────────────────────────────────────

class WeatherTool(BaseTool):
    name: str = "get_weather_context"
    description: str = (
        "Current weather at incident coordinates (Open-Meteo). "
        "Call for FLOODING, FIRE_HAZARD, ROAD_DAMAGE, POWER_OUTAGE, TRAFFIC_ACCIDENT. "
        "Returns precipitation, wind, temperature and priority_boost."
    )
    args_schema: Type[BaseModel] = CoordInput

    def _run(self, latitude: float, longitude: float) -> str:
        return json.dumps(get_weather_context(latitude, longitude))


class DistrictRiskTool(BaseTool):
    name: str = "get_district_risk_profile"
    description: str = (
        "Istanbul district risk profile: flood risk, industrial zone, chemical hazard. "
        "Always call this first — instant, no API cost."
    )
    args_schema: Type[BaseModel] = DistrictInput

    def _run(self, district: str) -> str:
        return json.dumps(get_district_risk_profile(district))


class TimeContextTool(BaseTool):
    name: str = "get_time_risk_context"
    description: str = (
        "Current Istanbul time context: rush hour, school hours, night, public holiday. "
        "Always call this — affects priority scoring and SLA."
    )
    args_schema: Type[BaseModel] = EmptyInput

    def _run(self) -> str:
        return json.dumps(get_time_risk_context())


class InfrastructureTool(BaseTool):
    name: str = "find_nearby_critical_infrastructure"
    description: str = (
        "Find hospitals, schools, fire stations near incident via Overpass/OSM. "
        "Call for priority >= 3. auto_escalate=true means P5 override required."
    )
    args_schema: Type[BaseModel] = CoordRadiusInput

    def _run(self, latitude: float, longitude: float, radius_m: int = 500) -> str:
        return json.dumps(find_nearby_critical_infrastructure(latitude, longitude, radius_m))


class GeolocationTool(BaseTool):
    name: str = "get_location_context"
    description: str = (
        "Reverse-geocode coordinates to street/neighbourhood (Nominatim). "
        "Call only if reported district seems inconsistent with coordinates."
    )
    args_schema: Type[BaseModel] = CoordInput

    def _run(self, latitude: float, longitude: float) -> str:
        return json.dumps(get_location_context(latitude, longitude))


class SimilarIncidentsTool(BaseTool):
    name: str = "check_similar_incidents"
    description: str = (
        "Check for similar open incidents in the same district+category via backend. "
        "Always call this — detects systemic issues. "
        "pattern_detected=true means infrastructure review is needed."
    )
    args_schema: Type[BaseModel] = SimilarInput

    def _run(self, district: str, category: str, days_back: int = 7) -> str:
        return json.dumps(check_similar_incidents(district, category, days_back))
