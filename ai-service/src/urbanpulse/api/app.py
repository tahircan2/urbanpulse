"""
urbanpulse.api.app — FastAPI application factory.

Creates and configures the ASGI application with middleware, routes, and lifespan.
Includes MCP (Model Context Protocol) client lifecycle management.
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
from urbanpulse.api.routes import mcp_route as mcp_router

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
        mcp_enabled=s.mcp_enabled,
    )

    # ── MCP Client Auto-Connect ───────────────────────────────────────────
    if s.mcp_enabled and s.mcp_auto_connect:
        try:
            from urbanpulse.mcp_client.manager import get_mcp_manager
            manager = get_mcp_manager()
            await manager.connect()
            logger.info(
                "mcp_client_auto_connected",
                tools_count=len(manager.tools),
                tool_names=[t.name for t in manager.tools],
            )
        except ImportError:
            logger.warning("mcp_sdk_not_installed", msg="pip install 'mcp[cli]' to enable MCP")
        except Exception as exc:
            logger.warning(
                "mcp_client_auto_connect_failed",
                error=str(exc),
                msg="Falling back to direct tool mode",
            )

    yield

    # ── MCP Client Disconnect ─────────────────────────────────────────────
    if s.mcp_enabled:
        try:
            from urbanpulse.mcp_client.manager import get_mcp_manager
            manager = get_mcp_manager()
            if manager.is_connected:
                await manager.disconnect()
                logger.info("mcp_client_disconnected_on_shutdown")
        except Exception as exc:
            logger.debug("mcp_shutdown_cleanup", error=str(exc))

    logger.info("urbanpulse_ai_stopped")


def create_app() -> FastAPI:
    s = get_settings()

    app = FastAPI(
        title="UrbanPulse AI Service",
        description="UrbanPulse AI — CrewAI + LangGraph dual pipeline with MCP integration",
        version="3.1.0",
        docs_url="/docs"     if not s.is_production else None,
        redoc_url="/redoc"   if not s.is_production else None,
        openapi_url="/openapi.json" if not s.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://localhost:4200", s.spring_backend_url],
        allow_methods=["*"],
        allow_headers=["*"],
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
    app.include_router(mcp_router.router,        prefix="/api")

    return app


app = create_app()
