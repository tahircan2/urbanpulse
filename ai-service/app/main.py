from __future__ import annotations
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config  import get_settings
from app.core.logging import get_logger, setup_logging
from app.routes       import pipeline as pipeline_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    s = get_settings()
    logger.info("urbanpulse_ai_starting", env=s.environment, backend=s.spring_backend_url)
    yield
    logger.info("urbanpulse_ai_stopped")


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="UrbanPulse AI Service",
        description="CrewAI multi-agent pipeline — Classifier → Planner → Monitor",
        version="3.0.0",
        docs_url="/docs"     if not s.is_production else None,
        redoc_url="/redoc"   if not s.is_production else None,
        openapi_url="/openapi.json" if not s.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", s.spring_backend_url],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Internal-Secret"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:  # type: ignore
        t0 = time.perf_counter()
        response = await call_next(request)
        logger.info("http", method=request.method, path=request.url.path,
                    status=response.status_code, ms=round((time.perf_counter()-t0)*1000, 1))
        return response

    app.include_router(pipeline_router.router, prefix="/api")
    return app


app = create_app()
