# UrbanPulse MCP — Incident Processing Flow

> Bu doküman, bir vatandaş şikayeti (incident) oluştuğu andan itibaren  
> MCP sisteminin tüm katmanlardan nasıl geçtiğini, adım adım açıklar.

---

## 1. Büyük Resim — Sistem Mimarisi

```mermaid
graph TB
    subgraph Frontend["Frontend (Angular)"]
        U["Vatandaş Formu"]
    end

    subgraph Backend["Backend (Spring Boot)"]
        API["REST API<br/>/api/incidents"]
        DB[("PostgreSQL")]
        CB["AI Callback"]
    end

    subgraph AI["AI Service (FastAPI + LangGraph)"]
        FAPI["FastAPI Gateway<br/>POST /api/langgraph/process"]
        LG["LangGraph Pipeline"]

        subgraph MCPClient["MCP Client"]
            MGR["MCPClientManager"]
            ADP["LangChain Adapter"]
        end

        subgraph MCPServer["MCP Server (subprocess)"]
            FM["FastMCP Engine"]
            T1["weather_context"]
            T2["district_risk_profile"]
            T3["time_risk_context"]
            T4["nearby_infrastructure"]
            T5["reverse_geocode"]
            T6["similar_incidents"]
        end
    end

    subgraph ExtAPIs["External APIs"]
        OM["Open-Meteo<br/>Weather"]
        NOM["Nominatim<br/>Geocoding"]
        OVP["Overpass<br/>Infrastructure"]
    end

    U -->|"HTTP POST"| API
    API -->|"Saves"| DB
    API -->|"HTTP POST + X-Internal-Secret"| FAPI
    FAPI --> LG
    LG -->|"get_active_tool_list()"| ADP
    ADP -->|"session.call_tool()"| MGR
    MGR ---|"stdio (JSON-RPC 2.0)"| FM
    FM --> T1 & T2 & T3 & T4 & T5 & T6
    T1 -->|"HTTP"| OM
    T5 -->|"HTTP"| NOM
    T4 -->|"HTTP"| OVP
    T6 -->|"HTTP"| API
    LG -->|"PipelineResult"| FAPI
    FAPI -->|"HTTP Response"| CB
    CB -->|"UPDATE"| DB

    style Frontend fill:#4f46e5,color:#fff
    style Backend fill:#059669,color:#fff
    style AI fill:#7c3aed,color:#fff
    style MCPClient fill:#6366f1,color:#fff
    style MCPServer fill:#8b5cf6,color:#fff
    style ExtAPIs fill:#0891b2,color:#fff
```

---

## 2. Incident Yaşam Döngüsü — Sequence Diagram

Aşağıdaki diyagram, bir "Kemer'de orman yangını" şikayetinin tüm sistemden geçiş sürecini gösterir:

```mermaid
sequenceDiagram
    actor Citizen as Vatandaş
    participant FE as Angular Frontend
    participant BE as Spring Boot
    participant FA as FastAPI Gateway
    participant LG as LangGraph Pipeline
    participant MC as MCP Client
    participant MS as MCP Server
    participant OM as Open-Meteo API

    Note over Citizen,OM: PHASE 1 — Incident Oluşturma
    Citizen->>FE: "Kemer'de duman ve alevler görülüyor"
    FE->>BE: POST /api/incidents
    BE->>BE: Incident kaydet (PostgreSQL)
    BE->>FA: POST /api/langgraph/process<br/>Header: X-Internal-Secret

    Note over FA,OM: PHASE 2 — LangGraph Pipeline Başlatma
    FA->>LG: run_langgraph_pipeline(incident)
    LG->>LG: State başlat (PipelineState)
    LG->>LG: input_guard_node → safe? evet

    Note over LG,OM: PHASE 3 — Classifier Node (MCP Tool Calls)
    LG->>LG: classify_node başladı
    LG->>MC: get_active_tool_list(prefer_mcp=True)
    MC-->>LG: MCP tools (6 adet), mode="mcp"
    LG->>LG: LLM'e tools bind et

    Note over MC,OM: Tool Call 1: District Risk Profile
    LG->>MC: call_tool("district_risk_profile", district="Kemer")
    MC->>MS: JSON-RPC → tools/call
    MS->>MS: get_district_risk_profile("Kemer")
    MS-->>MC: forest_risk: very_high
    MC-->>LG: ToolMessage(result)

    Note over MC,OM: Tool Call 2: Time Risk Context
    LG->>MC: call_tool("time_risk_context", {})
    MC->>MS: JSON-RPC → tools/call
    MS->>MS: get_time_risk_context()
    MS-->>MC: 21:30 Tuesday, not rush hour
    MC-->>LG: ToolMessage(result)

    Note over MC,OM: Tool Call 3: Weather Context
    LG->>MC: call_tool("weather_context", lat=36.59, lng=30.55)
    MC->>MS: JSON-RPC → tools/call
    MS->>OM: HTTP GET /v1/forecast
    OM-->>MS: temp=32°C, humidity=25%, wind=35km/h
    MS->>MS: fire_weather=true, priority_boost=+2
    MS-->>MC: weather data + boost
    MC-->>LG: ToolMessage(result)

    Note over LG,OM: PHASE 4 — LLM Classification Decision
    LG->>LG: LLM analiz: Kemer + forest_risk=very_high + fire_weather
    LG->>LG: Karar: FIRE_HAZARD, P5, override_reason="critical forest zone"

    Note over LG,OM: PHASE 5 — Planner Node
    LG->>LG: plan_node başladı
    LG->>MC: call_tool("similar_incidents", district="Kemer", category="FIRE_HAZARD")
    MC->>MS: JSON-RPC → tools/call
    MS->>BE: HTTP GET /api/incidents?district=Kemer&category=FIRE_HAZARD
    BE-->>MS: 2 benzer olay bulundu
    MS-->>MC: pattern_detected=false
    MC-->>LG: ToolMessage(result)
    LG->>LG: LLM: dept="Antalya İtfaiye Dairesi", SLA=1h

    Note over LG,FA: PHASE 6 — Monitor & Output Guard
    LG->>LG: monitor_node → "Fire department dispatched to Kemer with 1h response"
    LG->>LG: output_guard_node → safe=true

    Note over FA,BE: PHASE 7 — Response
    LG-->>FA: PipelineResult
    FA-->>BE: HTTP Response (category, priority, department, SLA)
    BE->>BE: Incident güncelle (PostgreSQL)
```

---

## 3. MCP İletişim Protokolü — JSON-RPC 2.0

MCP Client ve Server arasındaki iletişim standart JSON-RPC 2.0 mesajlarıyla yapılır. Bu mesajlar **stdio** (stdin/stdout) üzerinden iletilir:

```mermaid
sequenceDiagram
    participant C as MCP Client
    participant S as MCP Server

    Note over C,S: Handshake (initialize)
    C->>S: {"jsonrpc":"2.0","method":"initialize","id":1,<br/>"params":{"clientInfo":{"name":"urbanpulse-client"}}}
    S-->>C: {"jsonrpc":"2.0","id":1,"result":{<br/>"serverInfo":{"name":"urbanpulse-tools"},<br/>"capabilities":{"tools":{}}}}
    C->>S: {"jsonrpc":"2.0","method":"notifications/initialized"}

    Note over C,S: Tool Discovery (tools/list)
    C->>S: {"jsonrpc":"2.0","method":"tools/list","id":2}
    S-->>C: {"jsonrpc":"2.0","id":2,"result":{"tools":[<br/>{"name":"weather_context","description":"...","inputSchema":{...}},<br/>{"name":"district_risk_profile","description":"...","inputSchema":{...}},<br/>... 4 more tools ...]}}

    Note over C,S: Tool Execution (tools/call)
    C->>S: {"jsonrpc":"2.0","method":"tools/call","id":3,<br/>"params":{"name":"district_risk_profile",<br/>"arguments":{"district":"Kemer"}}}
    S-->>C: {"jsonrpc":"2.0","id":3,"result":{<br/>"content":[{"type":"text",<br/>"text":"{\"forest_risk\":\"very_high\",...}"}]}}
```

---

## 4. Dual-Mode Tool Resolution — Karar Akışı

Pipeline'ın MCP veya Direct mode arasında nasıl karar verdiğini gösteren akış:

```mermaid
flowchart TD
    A["Pipeline Node başladı<br/>(Classifier / Planner)"] --> B{"get_active_tool_list()<br/>çağrıldı"}
    B --> C{"MCP_ENABLED=true?"}
    C -->|Hayır| D["DIRECT MODE<br/>6 adet @tool wrapper"]
    C -->|Evet| E{"MCP Client<br/>connected?"}
    E -->|Hayır| F["Fallback:<br/>DIRECT MODE"]
    E -->|Evet| G{"MCP tools<br/>keşfedildi mi?"}
    G -->|Hayır| H["Fallback:<br/>DIRECT MODE"]
    G -->|Evet| I["MCP MODE<br/>6 adet MCP-adapted tool"]

    D --> J["LLM.bind_tools(tools)"]
    F --> J
    H --> J
    I --> J
    J --> K["invoke_with_tools() loop başladı"]

    style A fill:#7c3aed,color:#fff
    style I fill:#059669,color:#fff,stroke:#059669
    style D fill:#dc2626,color:#fff
    style F fill:#dc2626,color:#fff
    style H fill:#dc2626,color:#fff
    style J fill:#2563eb,color:#fff
    style K fill:#2563eb,color:#fff
```

---

## 5. MCP Client Lifecycle — Yaşam Döngüsü

```mermaid
stateDiagram-v2
    [*] --> DISCONNECTED: FastAPI başlatılıyor

    DISCONNECTED --> CONNECTING: lifespan → connect()
    CONNECTING --> CONNECTED: initialize() başarılı
    CONNECTING --> ERROR: Connection hatası

    CONNECTED --> CONNECTED: call_tool() başarılı
    CONNECTED --> ERROR: call_tool() hata
    CONNECTED --> DISCONNECTED: shutdown / disconnect()

    ERROR --> CONNECTING: /api/mcp/reconnect
    ERROR --> DISCONNECTED: shutdown

    state CONNECTED {
        [*] --> Idle
        Idle --> ToolCall: LangGraph tool isteği
        ToolCall --> Idle: Sonuç döndü
    }

    note right of CONNECTED
        Tools: 6 adet keşfedildi
        Transport: stdio
        Protocol: JSON-RPC 2.0
    end note
```

---

## 6. Tool Call Akışı — invoke_with_tools() Loop

Her node (classifier, planner) içindeki tool calling loop'u:

```mermaid
flowchart TD
    A["invoke_with_tools() başladı<br/>max_rounds=5"] --> B["LLM.invoke(messages)"]
    B --> C{"LLM tool_calls<br/>döndürdü mü?"}

    C -->|Hayır| D["Final text response<br/>döndür"]
    C -->|Evet| E["Her tool_call için:"]

    E --> F["Tool adını bul<br/>(weather_context vb.)"]
    F --> G{"Mode = MCP?"}

    G -->|MCP| H["MCP Client<br/>session.call_tool()"]
    H --> I["stdio → JSON-RPC → MCP Server"]
    I --> J["MCP Server tool çalıştır"]
    J --> K["Sonuç JSON olarak dön"]

    G -->|Direct| L["tool.run(args)<br/>Doğrudan Python çağrısı"]
    L --> K

    K --> M["ToolMessage oluştur<br/>messages listesine ekle"]
    M --> N{"rounds < max_rounds?"}

    N -->|Evet| B
    N -->|Hayır| O["Son LLM çağrısı<br/>'Provide final JSON response'"]
    O --> D

    style A fill:#7c3aed,color:#fff
    style H fill:#059669,color:#fff
    style L fill:#dc2626,color:#fff
    style D fill:#2563eb,color:#fff
```

---

## 7. MCP Dashboard — Monitoring Endpoint'leri

```mermaid
graph LR
    subgraph Dashboard["MCP Dashboard API"]
        S["/api/mcp/status<br/>GET"]
        T["/api/mcp/tools<br/>GET"]
        H["/api/mcp/history<br/>GET"]
        R["/api/mcp/reconnect<br/>POST"]
    end

    subgraph StatusResponse["Status Response"]
        S1["connection.state"]
        S2["connection.uptime_seconds"]
        S3["tools.discovered_count"]
        S4["telemetry.total_calls"]
        S5["telemetry.success_rate_pct"]
        S6["telemetry.avg_latency_ms"]
    end

    subgraph ToolsResponse["Tools Response"]
        T1["name: weather_context"]
        T2["name: district_risk_profile"]
        T3["name: time_risk_context"]
        T4["name: nearby_infrastructure"]
        T5["name: reverse_geocode"]
        T6["name: similar_incidents"]
    end

    subgraph HistoryResponse["History Response"]
        H1["tool_name + arguments"]
        H2["duration_ms"]
        H3["success / error"]
        H4["result_preview"]
    end

    S --> StatusResponse
    T --> ToolsResponse
    H --> HistoryResponse
    R -->|"disconnect + reconnect"| S

    style Dashboard fill:#7c3aed,color:#fff
    style StatusResponse fill:#1e3a5f,color:#fff
    style ToolsResponse fill:#1e3a5f,color:#fff
    style HistoryResponse fill:#1e3a5f,color:#fff
```

---

## 8. Gerçek Dünya Senaryosu — Adım Adım

Aşağıda **Kemer'de orman yangını** senaryosunun her katmanda nasıl işlendiği anlatılır:

### Adım 1: Vatandaş Bildirimi
```
Başlık: "Kemer'de duman ve alevler görülüyor"
Açıklama: "Kemer ilçesinde ormanlık alanda yoğun duman ve alevler var"
Kategori (kullanıcı): FIRE_HAZARD
Öncelik (kullanıcı): P3
Koordinat: 36.5937, 30.5567
İlçe: Kemer
```

### Adım 2: MCP Tool Call'ları (Classifier)

| Sıra | Tool | Sonuç |
|------|------|-------|
| 1 | `district_risk_profile("Kemer")` | forest_risk=**very_high**, tourism_zone=true, mountain_terrain=true |
| 2 | `time_risk_context()` | 21:30, Tuesday, not rush hour |
| 3 | `weather_context(36.59, 30.55)` | 32°C, humidity=25%, wind=35km/h → **fire_weather=true**, priority_boost=+2 |

### Adım 3: LLM Kararı (Classifier)
```json
{
  "category": "FIRE_HAZARD",
  "priority": 5,
  "confidence": 0.98,
  "reasoning": "Kemer has very high forest fire risk. Current weather shows fire conditions with high temperature, low humidity and strong wind. User reported P3 but this is critically underestimated.",
  "override_reason": "Critical forest fire zone with active fire weather conditions"
}
```

### Adım 4: MCP Tool Call'ları (Planner)

| Sıra | Tool | Sonuç |
|------|------|-------|
| 1 | `similar_incidents("Kemer", "FIRE_HAZARD")` | 0 benzer olay, pattern_detected=false |
| 2 | `district_risk_profile("Kemer")` | forest_risk=very_high |

### Adım 5: LLM Kararı (Planner)
```json
{
  "department": "Antalya İtfaiye Dairesi",
  "sla_hours": 1,
  "action_note": "Emergency fire response units dispatched to Kemer forest area. Aerial support requested due to mountainous terrain and difficult access. Tourism zone evacuation protocol initiated."
}
```

### Adım 6: Monitor Özeti
```
"Fire department units with aerial support are dispatched to Kemer with a 1-hour emergency response time due to critical forest fire conditions."
```

---

## 9. MCP vs Direct Mode Karşılaştırma

```mermaid
graph TD
    subgraph MCP["MCP Mode"]
        M1["LangGraph Node"] -->|"get_active_tool_list()"| M2["MCP Adapter"]
        M2 -->|"session.call_tool()"| M3["MCP Client Manager"]
        M3 -->|"JSON-RPC over stdio"| M4["MCP Server Process"]
        M4 -->|"import & execute"| M5["urbanpulse.tools.*"]
        M5 -->|"HTTP"| M6["External APIs"]
    end

    subgraph Direct["Direct Mode"]
        D1["LangGraph Node"] -->|"get_active_tool_list()"| D2["@tool wrappers"]
        D2 -->|"direct import"| D3["urbanpulse.tools.*"]
        D3 -->|"HTTP"| D4["External APIs"]
    end

    style MCP fill:#059669,color:#fff
    style Direct fill:#dc2626,color:#fff
```

| Özellik | Direct Mode | MCP Mode |
|---------|------------|----------|
| **Hız** | Daha hızlı (in-process) | Biraz yavaş (IPC overhead) |
| **Keşif** | Hardcoded import | Dinamik `tools/list` |
| **Protokol** | Python-specific | Standart JSON-RPC 2.0 |
| **İzolasyon** | Aynı process | Ayrı subprocess |
| **Taşınabilirlik** | Sadece LangChain | Herhangi bir MCP client |
| **Gözlemlenebilirlik** | Manuel loglama | Dahili telemetri |
| **Kullanım** | Fallback | Varsayılan (tercih edilen) |

---

## 10. Terminal Log Çıktısı Örneği

MCP modunda bir incident işlenirken terminalde görülen loglar:

```
[MCP-SERVER] INFO  UrbanPulse MCP Server v3.0.0 starting (transport=stdio)
[MCP-SERVER] INFO  Registered 6 tools, 2 resources
[MCP-SERVER] INFO  Processing request of type ListToolsRequest

[AI-SERVICE] INFO  mcp_client_connected tools_count=6
[AI-SERVICE] INFO  classifier_tools_resolved mode=mcp count=6
[AI-SERVICE] INFO  tool_loop_start mode=mcp max_rounds=5 available_tools=[...]

[AI-SERVICE] INFO  tool_call_dispatch mode=mcp tool=district_risk_profile round=1
[MCP-SERVER] INFO  Tool called: district_risk_profile(district=Kemer)
[MCP-SERVER] INFO  Tool result: district_risk_profile → FOREST FIRE RISK: very_high
[AI-SERVICE] INFO  mcp_tool_call_complete tool=district_risk_profile duration_ms=12

[AI-SERVICE] INFO  tool_call_dispatch mode=mcp tool=time_risk_context round=1
[MCP-SERVER] INFO  Tool called: time_risk_context()
[AI-SERVICE] INFO  mcp_tool_call_complete tool=time_risk_context duration_ms=8

[AI-SERVICE] INFO  tool_call_dispatch mode=mcp tool=weather_context round=1
[MCP-SERVER] INFO  Tool called: weather_context(lat=36.59, lng=30.55)
[MCP-SERVER] INFO  HTTP Request: GET https://api.open-meteo.com/v1/forecast "200 OK"
[AI-SERVICE] INFO  mcp_tool_call_complete tool=weather_context duration_ms=856

[AI-SERVICE] INFO  tool_loop_end mode=mcp rounds_used=1 reason=no_more_tool_calls
[AI-SERVICE] INFO  planner_tools_resolved mode=mcp count=6
[AI-SERVICE] INFO  langgraph_pipeline_complete category=FIRE_HAZARD priority=5 ms=4521
```
