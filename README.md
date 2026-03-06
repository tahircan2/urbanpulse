# UrbanPulse 🏙️

### Smart City Event & Traffic Management Platform

> Multi-agent AI platform for real-time urban incident management.
> Built with **Angular 17** · **Spring Boot 3** · **MySQL 8** · **LangGraph** (Phase 2)

[![Angular](https://img.shields.io/badge/Angular-17-DD0031?style=flat-square&logo=angular)](https://angular.io)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2-6DB33F?style=flat-square&logo=springboot)](https://spring.io)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql)](https://mysql.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## 📁 Repository Structure

```
urbanpulse/
├── frontend/                  # Angular 17 SPA
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # Home, Map, Report, Dashboard, About, Auth
│   │   │   ├── services/      # IncidentService, AuthService, WebSocketService
│   │   │   ├── models/        # Incident, Auth, API models
│   │   │   ├── interceptors/  # JWT + Error interceptors
│   │   │   └── guards/        # Auth + Staff route guards
│   │   ├── environments/      # dev / prod environment configs
│   │   └── styles.scss        # Global design system
│   ├── proxy.conf.json        # Dev proxy → localhost:8080
│   └── package.json
│
├── backend/                   # Spring Boot 3 REST API
│   └── src/main/java/com/urbanpulse/
│       ├── controller/        # Auth, Incident, AgentLog, Dashboard
│       ├── service/           # Business logic layer
│       ├── entity/            # JPA entities (User, Incident, AgentLog, Department)
│       ├── repository/        # Spring Data JPA repositories
│       ├── security/          # JWT filter, UserDetailsService
│       ├── config/            # Security, WebSocket, JPA configs
│       ├── dto/               # Request / Response DTOs
│       ├── enums/             # IncidentCategory, Status, Role, AgentName
│       ├── exception/         # Global exception handler
│       └── websocket/         # WebSocket event publisher
│
├── docs/
│   └── UrbanPulse_AI_Planning_Document.pdf
│
└── .github/workflows/
    ├── frontend-ci.yml        # Angular build + test
    └── backend-ci.yml         # Maven build + test
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+, Angular CLI 17
- Java 21+, Maven 3.9+
- MySQL 8.0+

### 1. Database Setup

```sql
CREATE DATABASE urbanpulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'urbanpulse_user'@'localhost' IDENTIFIED BY 'urbanpulse_pass';
GRANT ALL PRIVILEGES ON urbanpulse.* TO 'urbanpulse_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Backend

```bash
cd backend
mvn spring-boot:run
# API: http://localhost:8080/api
```

### 3. Frontend

```bash
cd frontend
npm install
npm start          # proxies /api → localhost:8080
# App: http://localhost:4200
```

---

## 🌐 Live Demo

- **Frontend:** https://urbanpulse.vercel.app
- **Backend API:** https://urbanpulse-api.up.railway.app/api

---

## 🔑 API Endpoints

| Method | Endpoint                 | Auth        | Description                  |
| ------ | ------------------------ | ----------- | ---------------------------- |
| POST   | `/auth/register`         | Public      | Register                     |
| POST   | `/auth/login`            | Public      | Login → JWT                  |
| GET    | `/incidents`             | Public      | List (filterable, paginated) |
| POST   | `/incidents`             | JWT         | Submit incident              |
| PATCH  | `/incidents/{id}/status` | STAFF/ADMIN | Update status                |
| GET    | `/agent-logs`            | STAFF/ADMIN | AI decision log              |
| GET    | `/dashboard/stats`       | STAFF/ADMIN | KPI summary                  |

---

## 🤖 AI Agent Architecture (Phase 2 — HW3)

```
New Incident
     │
     ▼
[Classifier Agent]  ──► Category + Priority (P1–P5)
     │
     ▼
[Planner Agent]     ──► Department assignment + SLA deadline
     │
     ▼
[Monitor Agent]     ──► SLA polling (every 15 min) + auto-escalation
```

Framework: **LangGraph** (Python) · Bridge: **FastAPI** · LLM: **OpenAI / Anthropic**

---

## 📋 Roadmap

| Phase      | Assignment                              | Status      |
| ---------- | --------------------------------------- | ----------- |
| Foundation | HW2 — Angular SPA + Spring Boot + MySQL | ✅ Complete |
| AI Agents  | HW3 — LangGraph pipeline integration    | 🔄 Planned  |
| Advanced   | HW4 — AutoGen + MCP tool integrations   | ⏳ Future   |

---

## 📄 Documentation

See [`docs/UrbanPulse_AI_Planning_Document.md`](docs/UrbanPulse_AI_Planning_Document.md)

## License

MIT © 2026 — AI Agent Systems Course, Spring 2026
