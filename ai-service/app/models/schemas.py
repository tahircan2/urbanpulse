from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums (mirror Spring Boot) ────────────────────────────────────────────────

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
    ASSIGN_PRIORITY     = "ASSIGN_PRIORITY"
    ROUTE_TO_DEPARTMENT = "ROUTE_TO_DEPARTMENT"
    GENERATE_REPORT     = "GENERATE_REPORT"


# ── Incident DTO (received from Spring Boot) ──────────────────────────────────

class IncidentDTO(BaseModel):
    id:              int
    title:           str
    description:     str
    category:        IncidentCategory
    status:          IncidentStatus
    priority:        int = Field(ge=1, le=5)
    latitude:        float
    longitude:       float
    district:        str
    reporter_name:   str
    reporter_email:  Optional[str] = None
    created_at:      datetime
    agent_processed: bool = False
    agent_notes:     Optional[str] = None

    model_config = {"populate_by_name": True}


# ── Agent Log ─────────────────────────────────────────────────────────────────

class AgentLogCreate(BaseModel):
    incident_id:     int
    incident_title:  str
    agent_name:      AgentName
    action:          AgentAction
    input_summary:   str
    output_summary:  str
    confidence:      Optional[float] = None
    processing_ms:   int
    success:         bool
    tools_called:    list[str] = Field(default_factory=list)
    override_reason: Optional[str] = None


class ValidationResult(BaseModel):
    """Guardrail validation outcome for an incoming incident."""
    valid:   bool
    reason:  str = ""


# ── API Requests / Responses ──────────────────────────────────────────────────

class ProcessIncidentRequest(BaseModel):
    incident: IncidentDTO


class PipelineResult(BaseModel):
    incident_id:         int
    classified_category: IncidentCategory
    classified_priority: int
    assigned_department: str
    sla_hours:           int
    agent_notes:         str
    agent_logs:          list[AgentLogCreate]
    success:             bool
    error:               Optional[str] = None


class HealthResponse(BaseModel):
    status:      str
    environment: str
    agents:      list[str]
    timestamp:   datetime


class AgentResultCallback(BaseModel):
    """Sent back to Spring Boot /api/incidents/{id}/agent-result"""
    incident_id:         int
    category:            IncidentCategory
    priority:            int
    assigned_department: str
    sla_hours:           int
    agent_notes:         str
    agent_processed:     bool = True
    logs:                list[AgentLogCreate]
