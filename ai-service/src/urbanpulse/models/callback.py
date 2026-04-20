"""
urbanpulse.models.callback — API request/response and callback models.
"""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from urbanpulse.models.enums import IncidentCategory
from urbanpulse.models.incident import IncidentDTO
from urbanpulse.models.pipeline import AgentLogCreate


class ProcessIncidentRequest(BaseModel):
    """Incoming request body from Spring Boot."""
    incident: IncidentDTO


class PipelineResult(BaseModel):
    """Re-exported for backwards compat — canonical in pipeline.py."""
    pass  # use from urbanpulse.models.pipeline


class HealthResponse(BaseModel):
    """GET /api/health response."""
    status:      str
    environment: str
    agents:      list[str]
    timestamp:   datetime


class AgentResultCallback(BaseModel):
    """Sent back to Spring Boot /api/incidents/{id}/agent-result."""
    incident_id:         int
    category:            IncidentCategory
    priority:            int
    assigned_department: str
    sla_hours:           int
    agent_notes:         str
    agent_processed:     bool = True
    logs:                list[AgentLogCreate]
