"""
urbanpulse.crewai_pipeline — CrewAI-based incident processing pipeline.

Structure follows official CrewAI project conventions:
    config/     → agents.yaml, tasks.yaml
    agents.py   → Agent factory methods
    tasks.py    → Task factory methods
    crew.py     → Crew assembly
    runner.py   → Pipeline execution
    tools.py    → BaseTool wrappers
"""
from urbanpulse.crewai_pipeline.runner import run_pipeline

__all__ = ["run_pipeline"]
