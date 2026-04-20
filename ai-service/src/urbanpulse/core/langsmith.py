"""
urbanpulse.core.langsmith — LangSmith tracing initialisation.

Configures environment variables consumed by langchain/langgraph at import time.
"""
import os
from urbanpulse.core.config import get_settings


def init_langsmith() -> None:
    """Configure LangSmith tracing via environment variables."""
    s = get_settings()
    if s.langsmith_api_key and s.langsmith_api_key != "your_langsmith_api_key_here":
        os.environ["LANGSMITH_TRACING"] = str(s.langsmith_tracing).lower()
        os.environ["LANGSMITH_API_KEY"] = str(s.langsmith_api_key)
        os.environ["LANGSMITH_PROJECT"] = str(s.langsmith_project)
