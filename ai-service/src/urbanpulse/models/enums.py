"""
urbanpulse.models.enums — Domain enumerations mirroring Spring Boot.
"""
from enum import Enum


class IncidentCategory(str, Enum):
    TRAFFIC_ACCIDENT = "TRAFFIC_ACCIDENT"
    ROAD_DAMAGE      = "ROAD_DAMAGE"
    FLOODING         = "FLOODING"
    POWER_OUTAGE     = "POWER_OUTAGE"
    FIRE_HAZARD      = "FIRE_HAZARD"
    VANDALISM        = "VANDALISM"
    NOISE_COMPLAINT  = "NOISE_COMPLAINT"
    OTHER            = "OTHER"


class IncidentStatus(str, Enum):
    PENDING     = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED    = "RESOLVED"
    CLOSED      = "CLOSED"


class AgentName(str, Enum):
    CLASSIFIER = "CLASSIFIER"
    PLANNER    = "PLANNER"
    MONITOR    = "MONITOR"


class AgentAction(str, Enum):
    CLASSIFY            = "CLASSIFY"
    ROUTE_TO_DEPARTMENT = "ROUTE_TO_DEPARTMENT"
    GENERATE_REPORT     = "GENERATE_REPORT"
