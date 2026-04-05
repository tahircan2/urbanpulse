"""
run.py — UrbanPulse AI Service başlatıcı (Windows uyumlu).

Kullanım: python run.py
"""
import sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "src")

# sys.path — ana process için
for p in [SRC, BASE]:
    if p not in sys.path:
        sys.path.insert(0, p)

# PYTHONPATH env var — Windows spawn process (uvicorn reload) için
existing = os.environ.get("PYTHONPATH", "")
os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [SRC, BASE, existing]))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=[BASE])
