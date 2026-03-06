# UrbanPulse 🏙️
### Smart City Event & Traffic Management Platform

> A multi-agent AI-powered platform for real-time urban incident management — built with Angular 17, Spring Boot 3, and LangGraph.

![Angular](https://img.shields.io/badge/Angular-17-DD0031?style=flat-square&logo=angular)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2-6DB33F?style=flat-square&logo=springboot)
![LangGraph](https://img.shields.io/badge/LangGraph-AI_Pipeline-FF6B35?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql)

---

## Overview

UrbanPulse enables citizens to report urban incidents — traffic accidents, road damage, flooding, power outages — through an intuitive web interface. A three-agent AI pipeline (Classifier → Planner → Monitor) autonomously classifies, prioritizes, and routes each report to the responsible municipal department, without requiring manual intervention.

This repository contains **Phase 1 (HW2)**: a fully functional Angular SPA with mock data, ready to be connected to the Spring Boot backend in Phase 2.

---

## Features

- **Live Map View** — Interactive Leaflet.js map displaying all active incidents across Istanbul with color-coded priority markers
- **Incident Report Form** — Citizen submission form with category selection, severity slider, and location picker
- **Authority Dashboard** — Filterable incidents table and AI Agent Decision Log with real-time status indicators
- **About / Architecture** — Full system architecture overview and AI pipeline documentation
- **Responsive Design** — Full mobile support across all pages

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 17 (Standalone Components, Signals) |
| Styling | SCSS with CSS Custom Properties |
| Map | Leaflet.js 1.9 |
| Icons | Font Awesome 6 |
| Fonts | Syne + Space Grotesk + JetBrains Mono |
| Backend (Phase 2) | Spring Boot 3.2, Spring Security, Spring WebSocket |
| Database (Phase 2) | PostgreSQL 16, Redis |
| AI Layer (Phase 2) | LangGraph, LangChain, FastAPI |

---

## Getting Started

### Prerequisites

- Node.js 18+ and npm 9+
- Angular CLI 17: `npm install -g @angular/cli`

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/urbanpulse.git
cd urbanpulse

# Install dependencies
npm install

# Start development server
ng serve

# Open in browser
# http://localhost:4200
```

### Production Build

```bash
ng build --configuration production
# Output: dist/urbanpulse/
```

### Deploy to GitHub Pages

```bash
ng add @angular/fire   # or use gh-pages
ng deploy
```

---

## Project Structure

```
src/
├── app/
│   ├── components/
│   │   ├── navbar/          # Fixed navigation bar
│   │   ├── home/            # Landing page with hero, stats, pipeline
│   │   ├── map/             # Leaflet interactive city map
│   │   ├── report/          # Citizen incident submission form
│   │   ├── dashboard/       # Authority panel + Agent Decision Log
│   │   └── about/           # Architecture overview & roadmap
│   ├── models/
│   │   ├── incident.model.ts
│   │   └── agent-log.model.ts
│   ├── services/
│   │   └── incident.service.ts   # Mock data service (Phase 1)
│   ├── app.routes.ts
│   ├── app.component.ts
│   └── app.config.ts
├── styles.scss              # Global design system (CSS variables, utilities)
└── index.html
```

---

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Hero section, live stats, recent incidents, AI pipeline overview |
| `/map` | Live Map | Interactive incident map with filtering and detail panel |
| `/report` | Report | Citizen incident submission form |
| `/dashboard` | Dashboard | Authority incident management + Agent Log |
| `/about` | About | Architecture, agent descriptions, roadmap |

---

## AI Agent Architecture (Phase 2)

The platform is designed around a **LangGraph three-agent pipeline**:

1. **Classifier Agent** — Analyses free-text descriptions and assigns category + priority (P1–P5)
2. **Planner Agent** — Routes incidents to departments based on workload and SLA constraints
3. **Monitor Agent** — Polls open incidents every 15 minutes for SLA breaches and auto-escalation

See the full planning document: [`AI_Planning_Document.pdf`](./docs/UrbanPulse_AI_Planning_Document.pdf)

---

## Development Roadmap

- **Phase 1 — HW2** ✅ Angular SPA, mock data, all 5 pages, GitHub deployment
- **Phase 2 — HW3** 🔄 LangGraph pipeline + Spring Boot backend integration
- **Phase 3 — HW4** ⏳ AutoGen multi-agent negotiation + MCP external API tools

---

## License

This project was developed as part of the AI Agent Systems course, Spring 2026.
