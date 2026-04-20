"""
urbanpulse.models.incident — Incident DTO received from Spring Boot.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from urbanpulse.models.enums import IncidentCategory, IncidentStatus


class IncidentDTO(BaseModel):
    """Incident data-transfer object — mirrors the Spring Boot entity."""
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
