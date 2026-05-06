"""
urbanpulse.api.routes.mcp_route — MCP Dashboard & Status API.

Provides REST endpoints for MCP observability:
    GET  /api/mcp/status   — Connection state, uptime, tool count, stats
    GET  /api/mcp/tools    — List of discovered MCP tools with schemas
    GET  /api/mcp/history  — Recent tool call history with telemetry
    POST /api/mcp/reconnect — Force reconnect to MCP server
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from urbanpulse.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["MCP Dashboard"])


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/mcp/status — Full MCP status dashboard
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/mcp/status")
async def mcp_status():
    """
    Returns comprehensive MCP connection status and telemetry.

    Response includes:
    - Connection state (connected/disconnected/error)
    - Server uptime
    - Number of discovered tools
    - Total/failed call counts and success rate
    - Average latency
    - MCP protocol metadata
    """
    try:
        from urbanpulse.mcp_client.manager import get_mcp_manager
        manager = get_mcp_manager()

        stats = manager.stats

        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mcp": {
                "protocol": "Model Context Protocol (MCP)",
                "transport": "stdio",
                "sdk": "mcp (official Anthropic Python SDK)",
                "spec_version": "2025-11-25",
            },
            "connection": {
                "state": stats["state"],
                "uptime_seconds": stats["uptime_seconds"],
            },
            "tools": {
                "discovered_count": stats["tools_discovered"],
                "tool_names": stats["server_info"].get("tool_names", []),
            },
            "telemetry": {
                "total_calls": stats["total_calls"],
                "failed_calls": stats["failed_calls"],
                "success_rate_pct": stats["success_rate"],
                "avg_latency_ms": stats["avg_latency_ms"],
            },
        }
    except ImportError:
        return {
            "success": False,
            "error": "MCP SDK not installed. Install with: pip install 'mcp[cli]'",
            "mcp": {"protocol": "Model Context Protocol (MCP)", "state": "unavailable"},
        }
    except Exception as exc:
        logger.error("mcp_status_error", error=str(exc))
        return {
            "success": False,
            "error": str(exc),
            "mcp": {"protocol": "Model Context Protocol (MCP)", "state": "error"},
        }


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/mcp/tools — Discovered tool definitions
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/mcp/tools")
async def mcp_tools():
    """
    Returns the list of tools discovered from the MCP server.

    Each tool includes its name, description, and JSON Schema input definition.
    This endpoint demonstrates MCP's dynamic tool discovery capability.
    """
    try:
        from urbanpulse.mcp_client.manager import get_mcp_manager
        manager = get_mcp_manager()

        if not manager.is_connected:
            return {
                "success": False,
                "error": "MCP client not connected",
                "tools": [],
            }

        tools_data = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in manager.tools
        ]

        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "mcp",
            "tools_count": len(tools_data),
            "tools": tools_data,
        }
    except ImportError:
        return {"success": False, "error": "MCP SDK not installed", "tools": []}
    except Exception as exc:
        logger.error("mcp_tools_error", error=str(exc))
        return {"success": False, "error": str(exc), "tools": []}


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/mcp/history — Recent tool call history
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/mcp/history")
async def mcp_history(limit: int = 20):
    """
    Returns the most recent MCP tool call records.

    Each record includes tool name, arguments, result preview,
    execution duration, and success/error status.

    Query params:
        limit: Maximum number of records to return (default: 20, max: 100)
    """
    try:
        from urbanpulse.mcp_client.manager import get_mcp_manager
        manager = get_mcp_manager()

        limit = min(max(limit, 1), 100)
        history = manager.call_history[-limit:]

        records = [
            {
                "tool_name": r.tool_name,
                "arguments": r.arguments,
                "result_preview": r.result_preview,
                "duration_ms": r.duration_ms,
                "success": r.success,
                "error": r.error,
                "timestamp": datetime.fromtimestamp(r.timestamp, tz=timezone.utc).isoformat(),
            }
            for r in reversed(history)  # Most recent first
        ]

        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_in_buffer": len(manager.call_history),
            "returned": len(records),
            "records": records,
        }
    except ImportError:
        return {"success": False, "error": "MCP SDK not installed", "records": []}
    except Exception as exc:
        logger.error("mcp_history_error", error=str(exc))
        return {"success": False, "error": str(exc), "records": []}


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/mcp/reconnect — Force reconnect
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/mcp/reconnect")
async def mcp_reconnect():
    """
    Force-disconnect and reconnect to the MCP server.

    Use this endpoint to recover from connection errors or to
    refresh the tool discovery after server updates.
    """
    try:
        from urbanpulse.mcp_client.manager import get_mcp_manager
        manager = get_mcp_manager()

        logger.info("mcp_reconnect_requested")

        # Disconnect if currently connected
        if manager.is_connected:
            await manager.disconnect()

        # Reconnect
        await manager.connect()

        return {
            "success": True,
            "message": "MCP client reconnected successfully",
            "tools_discovered": len(manager.tools),
            "tool_names": [t.name for t in manager.tools],
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="MCP SDK not installed")
    except Exception as exc:
        logger.error("mcp_reconnect_error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Reconnect failed: {exc}")
