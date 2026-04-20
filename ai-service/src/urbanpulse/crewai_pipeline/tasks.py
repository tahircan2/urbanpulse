"""
urbanpulse.crewai_pipeline.tasks — Task factory methods.

Each method loads its configuration from config/tasks.yaml and
returns a CrewAI Task wired to the correct agent and context.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from crewai import Task
from crewai.project import task

_CFG = Path(__file__).parent / "config"


def _yaml(filename: str) -> dict:
    """Load a YAML file from config/ next to this package."""
    with open(_CFG / filename, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TaskFactory:
    """Creates configured CrewAI tasks from YAML definitions."""

    @task
    def classify_incident(self) -> Task:
        cfg = _yaml("tasks.yaml")["classify_incident"]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=self.classifier(),
        )

    @task
    def plan_response(self) -> Task:
        cfg = _yaml("tasks.yaml")["plan_response"]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=self.planner(),
            context=[self.classify_incident()],
        )

    @task
    def summarize_pipeline(self) -> Task:
        cfg = _yaml("tasks.yaml")["summarize_pipeline"]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=self.monitor(),
            context=[self.classify_incident(), self.plan_response()],
        )
