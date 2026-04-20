"""
urbanpulse.crewai_pipeline.crew — Crew assembly.

Combines agents and tasks into a sequential CrewAI pipeline.
This is intentionally thin — agent/task definitions live in their own modules.
"""
from __future__ import annotations

from pathlib import Path

from crewai import Crew, Process
from crewai.project import CrewBase, crew

from urbanpulse.crewai_pipeline.agents import AgentFactory
from urbanpulse.crewai_pipeline.tasks  import TaskFactory

_CFG = Path(__file__).parent / "config"


@CrewBase
class UrbanPulseCrew(AgentFactory, TaskFactory):
    """Classifier → Planner → Monitor pipeline for new incidents."""

    agents_config = str(_CFG / "agents.yaml")
    tasks_config  = str(_CFG / "tasks.yaml")

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.classifier(), self.planner(), self.monitor()],
            tasks=[self.classify_incident(), self.plan_response(), self.summarize_pipeline()],
            process=Process.sequential,
            verbose=False,
        )
