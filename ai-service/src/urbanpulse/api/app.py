"""
urbanpulse.api.app — FastAPI application factory.

Creates and configures the ASGI application with middleware, routes, and lifespan.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from urbanpulse.core.config  import get_settings
from urbanpulse.core.logging import get_logger, setup_logging

from urbanpulse.api.routes import health as health_router
from urbanpulse.api.routes import crewai_route as crewai_router
from urbanpulse.api.routes import langgraph_route as langgraph_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    s = get_settings()
    from urbanpulse.core.langsmith import init_langsmith
    init_langsmith()
    logger.info(
        "urbanpulse_ai_starting",
        env=s.environment,
        backend=s.spring_backend_url,
    )
    yield
    logger.info("urbanpulse_ai_stopped")


def create_app() -> FastAPI:
    s = get_settings()

    app = FastAPI(
        title="UrbanPulse AI Service",
        description="UrbanPulse AI — CrewAI + LangGraph dual pipeline",
        version="3.0.0",
        docs_url="/docs"     if not s.is_production else None,
        redoc_url="/redoc"   if not s.is_production else None,
        openapi_url="/openapi.json" if not s.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", s.spring_backend_url],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Internal-Secret"],
    )

    # ── Request logging ───────────────────────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:  # type: ignore
        t0 = time.perf_counter()
        response = await call_next(request)
        logger.info(
            "http",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=round((time.perf_counter() - t0) * 1000, 1),
        )
        return response

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(health_router.router,     prefix="/api")
    app.include_router(crewai_router.router,     prefix="/api")
    app.include_router(langgraph_router.router,  prefix="/api")

    return app


app = create_app()
