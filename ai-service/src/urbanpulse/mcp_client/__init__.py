"""
urbanpulse.mcp_client — MCP Client package.

Manages the lifecycle of an MCP client connection to the UrbanPulse
MCP Server, and provides adapters to convert MCP tools into
LangChain-compatible tool objects for use in the LangGraph pipeline.

Architecture:
    LangGraph Pipeline
         ↓ uses
    MCP Client Adapter (LangChain Tool wrappers)
         ↓ delegates to
    MCP Client Manager (ClientSession lifecycle)
         ↕ stdio (JSON-RPC 2.0)
    MCP Server (urbanpulse.mcp_server)
"""
