<div align="center">

# 🏙️ UrbanPulse

**Real-time smart-city incident management. Citizens report, AI agents triage and route to the right municipal department.**

![Angular](https://img.shields.io/badge/Angular_19-DD0031?style=flat-square&logo=angular&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring_Boot_3-6DB33F?style=flat-square&logo=springboot&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-FF5A50?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-000000?style=flat-square)
![MySQL](https://img.shields.io/badge/MySQL_8-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

<img src="docs/screenshots/dashboard.png" alt="UrbanPulse command center" width="900">

</div>

## Highlights

| | |
|---|---|
| 🧠 **Agentic triage** | A CrewAI team (Classifier → Planner → Monitor) and a deterministic LangGraph pipeline decide priority and department |
| 🔌 **MCP tool layer** | Agents call tools over Model Context Protocol (JSON-RPC 2.0); the UI visualises every call live |
| ⚡ **Real time** | WebSockets push new incidents and AI decisions to every open screen, no refresh |
| 🗺️ **Live map** | Leaflet map of Antalya with priority-coloured, clustered markers |
| 🔒 **Secure** | Spring Security + JWT, three roles (Admin / Staff / Citizen), shared secret between backend and AI |

## Screenshots

| Live map | MCP architecture flow |
|:---:|:---:|
| <img src="docs/screenshots/map.png" width="440"> | <img src="docs/screenshots/mcp-flow.png" width="440"> |

## Architecture

```mermaid
graph LR
    A["Angular 19 + Leaflet"] -->|REST + WebSocket| B["Spring Boot 3 · Java 21"]
    B --> D[(MySQL 8)]
    B -->|incident| C["FastAPI AI service"]
    C --> E["CrewAI crew"]
    C --> F["LangGraph pipeline"]
    E & F <-->|MCP tools| M["MCP server"]
    C -->|decision callback| B
```

| Folder | Role |
|---|---|
| [`frontend/`](frontend) | Angular 19 SPA: signals, Tailwind, Leaflet |
| [`backend/`](backend) | REST API, JWT auth, WebSocket broker, persistence |
| [`ai-service/`](ai-service) | Agents, MCP server, LangGraph + CrewAI pipelines |

## Quick start

```bash
git clone https://github.com/tahircan2/urbanpulse.git && cd urbanpulse
export OPENAI_API_KEY=sk-...          # PowerShell: $env:OPENAI_API_KEY="sk-..."
docker compose up --build
```

Open **http://localhost:4200**. Demo logins (password `test123`, local dev only): `admin@urbanpulse.com`, `staff@urbanpulse.com`, `ahmet@example.com`.

## Docs

[Detailed README](docs/DETAILED_README.md) · [LangGraph report (PDF)](docs/UrbanPulse_LangGraph_Report.pdf) · [CrewAI report](docs/CREW_AI_REPORT.md) · [Contributing](CONTRIBUTING.md)
