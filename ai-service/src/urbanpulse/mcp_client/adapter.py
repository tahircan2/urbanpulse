"""
urbanpulse.mcp_client.adapter — MCP-to-LangChain Tool Adapter.

Bridges the MCP protocol with LangChain's tool interface, enabling
the LangGraph pipeline to seamlessly use MCP-discovered tools as
standard LangChain Tool objects.

Flow:
    1. MCPClientManager.connect() → discovers tools from MCP server
    2. This adapter reads the discovered tool definitions
    3. Converts each MCP tool to a LangChain StructuredTool
    4. LangGraph pipeline uses them identically to native @tool functions

This is the key integration layer that makes MCP transparent to the
existing LangGraph pipeline — no node code changes required.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from urbanpulse.core.logging import get_logger
from urbanpulse.mcp_client.manager import get_mcp_manager, MCPToolInfo

logger = get_logger(__name__)

# ── JSON Schema → Python type mapping ────────────────────────────────────────

_JSON_SCHEMA_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _build_pydantic_model(tool_info: MCPToolInfo) -> type[BaseModel]:
    """
    Dynamically create a Pydantic model from MCP tool's inputSchema.

    This is critical for LangChain integration: without an explicit
    args_schema, StructuredTool cannot map LLM-generated arguments
    to the underlying function's **kwargs, causing arguments to be lost.

    The MCP inputSchema follows JSON Schema format:
    {
        "type": "object",
        "properties": {
            "district": {"type": "string", "description": "..."},
            ...
        },
        "required": ["district"]
    }
    """
    schema = tool_info.input_schema or {}
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    if not properties:
        # Tool takes no arguments (e.g., time_risk_context)
        return create_model(f"{tool_info.name}Arguments")

    field_definitions: dict[str, Any] = {}

    for field_name, field_schema in properties.items():
        json_type = field_schema.get("type", "string")
        python_type = _JSON_SCHEMA_TYPE_MAP.get(json_type, str)
        description = field_schema.get("description", "")
        default = field_schema.get("default")

        if field_name in required_fields:
            # Required field — no default
            field_definitions[field_name] = (
                python_type,
                Field(description=description),
            )
        else:
            # Optional field with default
            field_definitions[field_name] = (
                Optional[python_type],
                Field(default=default, description=description),
            )

    model = create_model(f"{tool_info.name}Arguments", **field_definitions)
    return model


# ── Sync → Async Bridge ─────────────────────────────────────────────────────

def _create_sync_invoker(tool_name: str):
    """
    Create a synchronous wrapper that calls the MCP tool via the async manager.

    LangChain's tool.run() expects synchronous execution, but MCP client
    calls are async. The MCP ClientSession is bound to the event loop
    that created it (the main FastAPI loop), so we must dispatch coroutines
    to that specific loop using asyncio.run_coroutine_threadsafe().
    """
    def invoke(**kwargs: Any) -> str:
        manager = get_mcp_manager()

        if not manager.is_connected:
            return json.dumps({
                "error": f"MCP client not connected. Cannot call tool '{tool_name}'.",
                "summary": "MCP connection unavailable."
            })

        try:
            owner_loop = manager._loop
            if owner_loop is None or owner_loop.is_closed():
                raise RuntimeError("MCP session event loop is not available.")

            # Check if we're already on the owning loop
            try:
                running = asyncio.get_running_loop()
            except RuntimeError:
                running = None

            if running is owner_loop:
                # We're on the same loop — shouldn't normally happen
                # because LangChain calls tool.run() synchronously, but
                # handle it defensively with a nested event loop via thread.
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(_run_on_loop, owner_loop, tool_name, kwargs)
                    return future.result(timeout=30)
            else:
                # We're on a worker thread — schedule on the session's loop
                return _run_on_loop(owner_loop, tool_name, kwargs)

        except Exception as exc:
            logger.error("mcp_adapter_invoke_error", tool=tool_name, error=str(exc))
            return json.dumps({
                "error": str(exc),
                "summary": f"Tool '{tool_name}' call failed via MCP."
            })

    return invoke


def _run_on_loop(loop: asyncio.AbstractEventLoop, tool_name: str, kwargs: dict[str, Any]) -> str:
    """
    Schedule an MCP tool call on the session-owning event loop
    and block until the result is available.
    """
    manager = get_mcp_manager()
    coro = manager.call_tool(tool_name, kwargs)
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)


# ── Tool Builder ─────────────────────────────────────────────────────────────

def build_mcp_langchain_tools() -> list[StructuredTool]:
    """
    Convert all MCP-discovered tools into LangChain StructuredTool objects.

    This function reads the tool definitions that were discovered during
    MCPClientManager.connect() and wraps each one as a LangChain tool
    that delegates execution to the MCP server via JSON-RPC.

    Each tool gets a dynamically-generated Pydantic args_schema derived
    from the MCP inputSchema. This is essential — without it, LangChain
    cannot map LLM-generated arguments to the invoke function's **kwargs,
    causing arguments to be silently dropped.

    Returns:
        List of LangChain StructuredTool objects ready for LangGraph pipeline use.
        Returns empty list if MCP client is not connected.
    """
    manager = get_mcp_manager()

    if not manager.is_connected:
        logger.warning("mcp_adapter_not_connected", msg="Cannot build tools — MCP client not connected")
        return []

    langchain_tools: list[StructuredTool] = []

    for tool_info in manager.tools:
        invoker = _create_sync_invoker(tool_info.name)

        # Build Pydantic args_schema from MCP inputSchema
        try:
            args_schema = _build_pydantic_model(tool_info)
        except Exception as exc:
            logger.warning(
                "mcp_args_schema_build_failed",
                tool=tool_info.name,
                error=str(exc),
            )
            args_schema = None

        # Build the LangChain StructuredTool with proper args_schema
        lc_tool = StructuredTool.from_function(
            func=invoker,
            name=tool_info.name,
            description=tool_info.description,
            args_schema=args_schema,
        )

        langchain_tools.append(lc_tool)
        logger.debug(
            "mcp_tool_adapted",
            tool=tool_info.name,
            args_schema=args_schema.model_json_schema() if args_schema else {},
        )

    logger.info(
        "mcp_tools_adapted",
        count=len(langchain_tools),
        tools=[t.name for t in langchain_tools],
    )

    return langchain_tools
