"""
urbanpulse.models.pipeline — Pipeline execution result models.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from urbanpulse.models.enums import AgentAction, AgentName, IncidentCategory


class AgentLogCreate(BaseModel):
    """One log entry per agent execution step."""
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


class PipelineResult(BaseModel):
    """Final result returned by both CrewAI and LangGraph pipelines."""
    incident_id:         int
    classified_category: IncidentCategory
    classified_priority: int
    assigned_department: str
    sla_hours:           int
    agent_notes:         str
    agent_logs:          list[AgentLogCreate]
    success:             bool
    error:               Optional[str] = None
