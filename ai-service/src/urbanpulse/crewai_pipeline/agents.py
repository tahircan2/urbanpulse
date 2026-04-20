"""
urbanpulse.crewai_pipeline.agents — Agent factory methods.

Each method loads its configuration from config/agents.yaml and
returns a fully-configured CrewAI Agent with tools and LLM.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from crewai import Agent, LLM
from crewai.project import agent

from urbanpulse.core.config import get_settings
from urbanpulse.crewai_pipeline.tools import (
    DistrictRiskTool,
    GeolocationTool,
    InfrastructureTool,
    SimilarIncidentsTool,
    TimeContextTool,
    WeatherTool,
)

_CFG = Path(__file__).parent / "config"


def _yaml(filename: str) -> dict:
    """Load a YAML file from config/ next to this package."""
    with open(_CFG / filename, encoding="utf-8") as f:
        return yaml.safe_load(f)


class AgentFactory:
    """Creates configured CrewAI agents from YAML definitions."""

    @agent
    def classifier(self) -> Agent:
        s   = get_settings()
        cfg = _yaml("agents.yaml")["classifier"]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            tools=[
                DistrictRiskTool(),
                TimeContextTool(),
                WeatherTool(),
                InfrastructureTool(),
                GeolocationTool(),
            ],
            llm=LLM(model=s.classifier_model, api_key=s.openai_api_key, max_tokens=512),
            verbose=False,
            allow_delegation=False,
            max_iter=s.tool_max_rounds,
        )

    @agent
    def planner(self) -> Agent:
        s   = get_settings()
        cfg = _yaml("agents.yaml")["planner"]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            tools=[
                SimilarIncidentsTool(),
                DistrictRiskTool(),
                TimeContextTool(),
            ],
            llm=LLM(model=s.planner_model, api_key=s.openai_api_key, max_tokens=512),
            verbose=False,
            allow_delegation=False,
            max_iter=s.tool_max_rounds,
        )

    @agent
    def monitor(self) -> Agent:
        s   = get_settings()
        cfg = _yaml("agents.yaml")["monitor"]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            tools=[],
            llm=LLM(model=s.monitor_model, api_key=s.openai_api_key, max_tokens=200),
            verbose=False,
            allow_delegation=False,
            max_iter=1,
        )
