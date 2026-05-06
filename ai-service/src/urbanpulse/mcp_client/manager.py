"""
urbanpulse.mcp_client.manager — MCP Client Session Manager.

Manages the full lifecycle of an MCP client connection to the
UrbanPulse MCP Server via stdio transport:
    1. Spawns the MCP server as a subprocess
    2. Establishes a ClientSession with JSON-RPC 2.0 handshake
    3. Discovers available tools via tools/list
    4. Provides call_tool() for individual tool invocations
    5. Tracks connection state, call history, and telemetry
    6. Handles graceful shutdown and error recovery

Thread Safety:
    This manager is designed for async usage. The connect/disconnect
    methods should be called from the FastAPI lifespan context.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from urbanpulse.core.logging import get_logger

logger = get_logger(__name__)


# ── Data Models ───────────────────────────────────────────────────────────────

class ConnectionState(str, Enum):
    """MCP client connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING   = "connecting"
    CONNECTED    = "connected"
    ERROR        = "error"


@dataclass
class ToolCallRecord:
    """Record of a single MCP tool invocation for telemetry."""
    tool_name: str
    arguments: dict[str, Any]
    result_preview: str
    duration_ms: int
    success: bool
    timestamp: float = field(default_factory=time.time)
    error: str | None = None


@dataclass
class MCPToolInfo:
    """Parsed MCP tool definition from tools/list response."""
    name: str
    description: str
    input_schema: dict[str, Any]


# ── MCP Client Manager ───────────────────────────────────────────────────────

class MCPClientManager:
    """
    Manages the lifecycle and state of an MCP client connection.

    This is a singleton-style manager that maintains:
    - The subprocess-spawned MCP server
    - The active ClientSession
    - Tool definitions discovered from the server
    - Complete call history for observability / dashboard
    """

    def __init__(self) -> None:
        self._state: ConnectionState = ConnectionState.DISCONNECTED
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._tools: list[MCPToolInfo] = []
        self._call_history: list[ToolCallRecord] = []
        self._connected_at: float | None = None
        self._server_info: dict[str, Any] = {}
        self._total_calls: int = 0
        self._failed_calls: int = 0
        self._lock = asyncio.Lock()
        # The event loop the MCP session is bound to (set during connect)
        self._loop: asyncio.AbstractEventLoop | None = None

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._state == ConnectionState.CONNECTED and self._session is not None

    @property
    def tools(self) -> list[MCPToolInfo]:
        return list(self._tools)

    @property
    def call_history(self) -> list[ToolCallRecord]:
        return list(self._call_history)

    @property
    def stats(self) -> dict[str, Any]:
        """Return aggregated telemetry for the dashboard."""
        uptime_s = (time.time() - self._connected_at) if self._connected_at else 0
        avg_ms = 0
        if self._call_history:
            avg_ms = sum(r.duration_ms for r in self._call_history) / len(self._call_history)

        return {
            "state": self._state.value,
            "uptime_seconds": round(uptime_s, 1),
            "tools_discovered": len(self._tools),
            "total_calls": self._total_calls,
            "failed_calls": self._failed_calls,
            "success_rate": (
                round((self._total_calls - self._failed_calls) / self._total_calls * 100, 1)
                if self._total_calls > 0 else 0.0
            ),
            "avg_latency_ms": round(avg_ms, 1),
            "server_info": self._server_info,
        }

    # ── Connection Lifecycle ──────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Spawn the MCP server subprocess and establish a ClientSession.

        This method:
        1. Resolves the path to the MCP server module
        2. Creates StdioServerParameters for subprocess launch
        3. Opens stdio transport (spawns server process)
        4. Initializes the MCP protocol handshake
        5. Discovers available tools via tools/list
        """
        async with self._lock:
            if self.is_connected:
                logger.info("mcp_client_already_connected")
                return

            self._state = ConnectionState.CONNECTING
            logger.info("mcp_client_connecting", transport="stdio")

            try:
                # Resolve server module path
                server_module = "urbanpulse.mcp_server.server"

                # Determine the Python executable (use the same one running this process)
                python_exec = sys.executable

                # Build server parameters for stdio transport
                server_params = StdioServerParameters(
                    command=python_exec,
                    args=["-m", server_module],
                    env={
                        **os.environ,
                        "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
                    },
                )

                # Create the exit stack for managed context cleanup
                self._exit_stack = AsyncExitStack()
                await self._exit_stack.__aenter__()

                # Connect via stdio transport → spawns server subprocess
                stdio_transport = await self._exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read_stream, write_stream = stdio_transport

                # Create and initialize the MCP ClientSession
                self._session = await self._exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await self._session.initialize()

                # Discover tools from the server
                tools_response = await self._session.list_tools()
                self._tools = [
                    MCPToolInfo(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                    )
                    for tool in tools_response.tools
                ]

                self._connected_at = time.time()
                self._state = ConnectionState.CONNECTED
                # Remember which event loop owns the session
                self._loop = asyncio.get_running_loop()

                # Store server info
                self._server_info = {
                    "transport": "stdio",
                    "tools_count": len(self._tools),
                    "tool_names": [t.name for t in self._tools],
                }

                logger.info(
                    "mcp_client_connected",
                    tools_count=len(self._tools),
                    tool_names=[t.name for t in self._tools],
                )

            except Exception as exc:
                self._state = ConnectionState.ERROR
                logger.error("mcp_client_connection_failed", error=str(exc))
                # Clean up on failure
                if self._exit_stack:
                    try:
                        await self._exit_stack.aclose()
                    except Exception:
                        pass
                    self._exit_stack = None
                self._session = None
                raise

    async def disconnect(self) -> None:
        """Gracefully close the MCP client session and terminate the server subprocess."""
        async with self._lock:
            if self._exit_stack:
                try:
                    await self._exit_stack.aclose()
                    logger.info("mcp_client_disconnected")
                except Exception as exc:
                    logger.warning("mcp_client_disconnect_error", error=str(exc))
                finally:
                    self._exit_stack = None
                    self._session = None
                    self._state = ConnectionState.DISCONNECTED
                    self._connected_at = None
                    self._loop = None

    # ── Tool Invocation ───────────────────────────────────────────────────

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """
        Invoke a tool on the MCP server via the active ClientSession.

        Records the call in history for dashboard telemetry.

        Args:
            name: The tool name as registered on the server
            arguments: Dictionary of tool arguments

        Returns:
            The tool result as a string

        Raises:
            RuntimeError: If the client is not connected
        """
        if not self.is_connected or self._session is None:
            raise RuntimeError("MCP client is not connected. Call connect() first.")

        t0 = time.monotonic()
        self._total_calls += 1

        logger.info("mcp_tool_call_start", tool=name, arguments=arguments)

        try:
            result = await self._session.call_tool(name, arguments)

            duration_ms = int((time.monotonic() - t0) * 1000)

            # Extract text content from MCP result
            result_text = ""
            if result.content:
                for block in result.content:
                    if hasattr(block, "text"):
                        result_text += block.text

            # Record in history
            record = ToolCallRecord(
                tool_name=name,
                arguments=arguments,
                result_preview=result_text[:200] if result_text else "",
                duration_ms=duration_ms,
                success=not result.isError if hasattr(result, 'isError') else True,
            )
            self._call_history.append(record)

            # Keep history bounded (last 100 calls)
            if len(self._call_history) > 100:
                self._call_history = self._call_history[-100:]

            logger.info(
                "mcp_tool_call_complete",
                tool=name,
                duration_ms=duration_ms,
                result_preview=result_text[:100] if result_text else "empty",
            )

            return result_text

        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._failed_calls += 1

            record = ToolCallRecord(
                tool_name=name,
                arguments=arguments,
                result_preview="",
                duration_ms=duration_ms,
                success=False,
                error=str(exc),
            )
            self._call_history.append(record)

            logger.error("mcp_tool_call_error", tool=name, error=str(exc), duration_ms=duration_ms)
            raise


# ── Singleton Instance ────────────────────────────────────────────────────────

_manager_instance: MCPClientManager | None = None


def get_mcp_manager() -> MCPClientManager:
    """Get or create the singleton MCPClientManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MCPClientManager()
    return _manager_instance
