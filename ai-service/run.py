"""
run.py — UrbanPulse AI Service entry point (Windows compatible).

Usage: python run.py
"""
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "src")

# sys.path — main source root
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# PYTHONPATH env var — for Uvicorn reload & subprocesses
existing = os.environ.get("PYTHONPATH", "")
os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [SRC, existing]))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "urbanpulse.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[SRC],
    )
