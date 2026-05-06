# UrbanPulse MCP Integration Report 🔌

## Model Context Protocol (MCP) — Technical Implementation

> **Protocol Version:** 2025-11-25  
> **SDK:** `mcp` v1.26.0 (Official Anthropic Python SDK)  
> **Transport:** stdio (JSON-RPC 2.0)  
> **Integration Mode:** Dual-mode (MCP + Direct fallback)

---

## 1. What is MCP?

**Model Context Protocol (MCP)** is an open standard developed by Anthropic for connecting AI models to external tools and data sources. It provides a **universal, standardized interface** — similar to how USB-C provides a universal hardware connector.

### Core Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        MCP HOST                                  │
│                  (FastAPI + LangGraph Pipeline)                   │
│                                                                  │
│  ┌─────────────┐    ┌─────────────────────────────────────────┐  │
│  │  MCP CLIENT  │◄──►│          MCP SERVER                     │  │
│  │  (adapter)   │    │    (urbanpulse.mcp_server)              │  │
│  └──────┬───────┘    │                                         │  │
│         │ JSON-RPC   │  ┌──────────┐  ┌──────────────────────┐ │  │
│         │ over stdio │  │ Tool 1:  │  │ Tool 4:              │ │  │
│         ▼            │  │ Weather  │  │ Infrastructure       │ │  │
│  ┌──────────────┐    │  └──────────┘  └──────────────────────┘ │  │
│  │  LangGraph   │    │  ┌──────────┐  ┌──────────────────────┐ │  │
│  │  Pipeline    │    │  │ Tool 2:  │  │ Tool 5:              │ │  │
│  │  (Classifier │    │  │ District │  │ Geocoding            │ │  │
│  │   Planner    │    │  │ Risk     │  └──────────────────────┘ │  │
│  │   Monitor)   │    │  └──────────┘  ┌──────────────────────┐ │  │
│  └──────────────┘    │  ┌──────────┐  │ Tool 6:              │ │  │
│                      │  │ Tool 3:  │  │ Similar Incidents    │ │  │
│                      │  │ Time Ctx │  └──────────────────────┘ │  │
│                      │  └──────────┘                           │  │
│                      └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Why MCP?

| Feature | Without MCP (Direct) | With MCP |
|---------|---------------------|----------|
| **Tool Discovery** | Hardcoded imports | Dynamic at runtime |
| **Protocol** | Framework-specific | Universal JSON-RPC 2.0 |
| **Portability** | LangChain only | Any AI framework |
| **Server Independence** | Same process | Separate process (can be remote) |
| **Observability** | Manual logging | Built-in protocol telemetry |

---

## 2. Implementation Structure

```
ai-service/src/urbanpulse/
├── mcp_server/                     # MCP SERVER (Tool Provider)
│   ├── __init__.py
│   └── server.py                   # FastMCP server — exposes 6 tools + 2 resources
│
├── mcp_client/                     # MCP CLIENT (Tool Consumer)
│   ├── __init__.py
│   ├── manager.py                  # Connection lifecycle, session, telemetry
│   └── adapter.py                  # MCP tools → LangChain StructuredTool bridge
│
├── langgraph_pipeline/
│   ├── tools.py                    # DUAL MODE — MCP or Direct tool resolution
│   └── nodes/
│       ├── utils.py                # MCP-aware tool loop with structured logging
│       ├── classifier.py           # Updated — uses get_active_tool_list()
│       └── planner.py              # Updated — uses get_active_tool_list()
│
├── api/
│   ├── app.py                      # MCP lifecycle (auto-connect/disconnect)
│   └── routes/
│       └── mcp_route.py            # Dashboard endpoints (/api/mcp/*)
│
└── core/
    └── config.py                   # MCP_ENABLED, MCP_AUTO_CONNECT settings
```

---

## 3. MCP Server — Tool Exposure

The MCP Server uses the **FastMCP** decorator pattern from the official SDK to register tools:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("urbanpulse-tools", version="3.0.0")

@mcp.tool()
def weather_context(latitude: float, longitude: float) -> str:
    """Get current weather conditions at incident coordinates."""
    from urbanpulse.tools.weather import get_weather_context
    return json.dumps(get_weather_context(latitude, longitude))
```

### Registered Tools (6)

| # | Tool Name | External API | Purpose |
|---|-----------|-------------|---------|
| 1 | `weather_context` | Open-Meteo | Real-time weather conditions |
| 2 | `district_risk_profile` | Static DB | Antalya district risk data |
| 3 | `time_risk_context` | Pure Python | Time-based risk factors |
| 4 | `nearby_infrastructure` | Overpass/OSM | Critical facilities proximity |
| 5 | `reverse_geocode` | Nominatim | Coordinate-to-address lookup |
| 6 | `similar_incidents` | Spring Boot | Incident pattern detection |

### Registered Resources (2)

| Resource URI | Content |
|-------------|---------|
| `urbanpulse://districts` | All 13 Antalya district risk profiles |
| `urbanpulse://server-info` | Server metadata and capabilities |

---

## 4. MCP Client — Tool Consumption

### Connection Flow

```
1. FastAPI starts (lifespan)
       ↓
2. MCPClientManager.connect()
       ↓
3. StdioServerParameters → spawn server subprocess
       ↓
4. stdio_client() → open read/write streams
       ↓
5. ClientSession.initialize() → JSON-RPC handshake
       ↓
6. session.list_tools() → discover 6 tools
       ↓
7. Tools available for LangGraph pipeline
```

### Dual-Mode Operation

```python
def get_active_tools(prefer_mcp=True):
    if prefer_mcp and mcp_client.is_connected:
        return build_mcp_langchain_tools(), "mcp"     # MCP mode
    return DIRECT_TOOLS, "direct"                      # Fallback mode
```

---

## 5. Dashboard API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mcp/status` | GET | Connection state, uptime, telemetry |
| `/api/mcp/tools` | GET | Discovered tool definitions with schemas |
| `/api/mcp/history` | GET | Recent tool call records |
| `/api/mcp/reconnect` | POST | Force reconnect to MCP server |

### Example: GET /api/mcp/status

```json
{
  "success": true,
  "mcp": {
    "protocol": "Model Context Protocol (MCP)",
    "transport": "stdio",
    "sdk": "mcp (official Anthropic Python SDK)",
    "spec_version": "2025-11-25"
  },
  "connection": {
    "state": "connected",
    "uptime_seconds": 3421.5
  },
  "tools": {
    "discovered_count": 6,
    "tool_names": [
      "weather_context",
      "district_risk_profile",
      "time_risk_context",
      "nearby_infrastructure",
      "reverse_geocode",
      "similar_incidents"
    ]
  },
  "telemetry": {
    "total_calls": 24,
    "failed_calls": 0,
    "success_rate_pct": 100.0,
    "avg_latency_ms": 156.3
  }
}
```

---

## 6. MCP Process Flow — Step by Step

When an incident arrives, here's what happens with MCP enabled:

```
Step 1: Incident arrives at /api/langgraph/process
             ↓
Step 2: LangGraph pipeline starts
             ↓
Step 3: Classifier node calls get_active_tool_list()
        → Returns MCP tools (6 tools discovered from server)
             ↓
Step 4: LLM decides to call "district_risk_profile"
             ↓
Step 5: MCP Client sends JSON-RPC request:
        {"jsonrpc":"2.0","method":"tools/call",
         "params":{"name":"district_risk_profile",
                   "arguments":{"district":"Kemer"}}}
             ↓  (stdio pipe)
Step 6: MCP Server receives, executes tool logic
             ↓
Step 7: MCP Server returns JSON-RPC response:
        {"jsonrpc":"2.0","result":{"content":[
          {"type":"text","text":"{\"forest_risk\":\"very_high\",...}"}
        ]}}
             ↓  (stdio pipe)
Step 8: MCP Client extracts result text
             ↓
Step 9: Result passed back to LLM as ToolMessage
             ↓
Step 10: LLM uses enriched context for classification
         → "Kemer + forest fire risk → P5 FIRE_HAZARD"
```

---

## 7. Configuration

```env
# .env
MCP_ENABLED=true           # Enable MCP dual-mode
MCP_AUTO_CONNECT=true      # Auto-connect on startup
```

| Setting | Default | Description |
|---------|---------|-------------|
| `MCP_ENABLED` | `true` | Use MCP tools when available, fall back to direct |
| `MCP_AUTO_CONNECT` | `true` | Connect to MCP server during FastAPI startup |

---

## 8. Key Benefits Demonstrated

1. **Standardization** — Tools follow the universal MCP protocol, not locked to LangChain
2. **Dynamic Discovery** — Tools are discovered at runtime, not hardcoded
3. **Process Isolation** — MCP server runs as a separate process
4. **Observability** — Every tool call is logged with duration, arguments, and results
5. **Graceful Degradation** — Falls back to direct mode if MCP is unavailable
6. **Reusability** — The same MCP server can serve Claude Desktop, VS Code, or any MCP client
