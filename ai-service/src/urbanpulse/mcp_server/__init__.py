"""
urbanpulse.mcp_server — MCP (Model Context Protocol) Server package.

Exposes UrbanPulse's core tools as a standards-compliant MCP server
using the official Anthropic MCP Python SDK (FastMCP).

Architecture:
    MCP Client (LangGraph Pipeline)
         ↕  stdio (JSON-RPC 2.0)
    MCP Server (this package)
         ↓
    urbanpulse.tools.*  (core business logic)
"""
