# UrbanPulse 🏙️ (Next-Gen Smart City Incident Management)

UrbanPulse is an **AI-Powered**, **Real-Time** full-stack software ecosystem designed to manage urban emergencies and citizen reports in modern cities.

All data, ranging from street issues reported by citizens (e.g., burst pipes, power outages) to life-threatening emergencies (e.g., fires, accidents), first enters the Backend system. It is then forwarded to a specially trained **CrewAI multi-agent artificial intelligence team**. The AI team filters the report, determines its true priority, and instantly routes it to the most appropriate public institution (relevant municipal department, fire brigade, water and wastewater administration, etc.), returning the decision back to the system immediately.

---

## 🚀 Key Features

- **🧠 Autonomous Agent Decision Making:** Instead of classic if-else assignments; a smart **CrewAI** model contextually analyzes metrics such as the tourism season, local vegetation (forest fire risk), and weather conditions.
- **⚡ Real-Time (WebSockets) Communication:** As soon as incidents are dropped on the map or the AI makes a decision, all citizen and operator panels are updated instantly without the need to refresh the page.
- **🛡️ Flawless Interface:** A Dashboard built using modern Angular 19, responsive, state-managed with Signal architecture, and powered by interactive Leaflet maps.
- **🔒 Secure Architecture:** Spring Security-protected Backend, JWT-Based Authentication mechanisms, and a special 'Internal Secret' validation between the AI and the Backend.

---

## 🏗️ Architecture and Tech Stack

The project is structured around 3 main folders within an enterprise-level Monorepo architecture:

### 1. Frontend (Angular 19)
- **Type:** Dynamic Single Page Application (SPA)
- **Technologies:** Angular 19, Standalone Components, Signals, RxJS, Tailwind CSS (Design), Leaflet.js (Map Architecture).
- **Role:** The point where citizens and administrators interact with the system. It listens to live WebSockets and shows system activity (new reports, status changes) as "Marker" updates on the live map instantly. The design is highly modern with a dark theme.

### 2. Backend (Spring Boot 3 & Java 19)
- **Type:** RESTful API and Message Broker
- **Technologies:** Java 19, Spring Boot 3.x, Hibernate / JPA, Spring Security (JWT), Spring WebSockets, MySQL.
- **Role:** The heart and database manager of the system. It manages business rules, handles JWT validation, pumps data to the AI Service, and instantly pushes event changes to all open screens via WebSockets.

### 3. AI Service (Python & CrewAI)
- **Type:** Async AI NLP Service 
- **Technologies:** Python 3.12+, FastAPI, CrewAI, Pydantic, Gunicorn/Uvicorn.
- **Role:** The "Brain" of the ecosystem. When Spring Boot catches a report, it sends an HTTP request to this service. Here, an autonomous team of 3 agents (Classifier, Planner, Monitor) works sequentially. It examines the incoming situation, catches manipulations and fake urgency notifications, filters them logically, and posts its decisions back to the Backend within seconds.
- _*(For detailed information on how the agents work, check the `/ai-service/README.md` guide).*_

---

## 🛠️ Installation and Execution

Each leg of the project is designed to run synchronously in separate terminal environments.

### Prerequisites
- **Node.js** (v18+)
- **Java** (v19 JDK) & Maven
- **Python** (3.12+)
- **MySQL** Database Server (Running locally)

### Environment Variables
You need to fill in your DB connection password in `backend/src/main/resources/application.properties`,
and the `OPENAI_API_KEY` variable in `ai-service/.env`.

### Step 1: Starting the Backend
```bash
cd backend
mvn clean install
mvn spring-boot:run
```
*(The Backend will successfully start on port 8080.)*

### Step 2: Starting the AI Service
```bash
cd ai-service
uv venv
uv pip install -r requirements.txt
python run.py
```
*(The AI service will run locally with Uvicorn.)*

### Step 3: Starting the Frontend
```bash
cd frontend
npm install
npm start
```
*(The web application will be available at http://localhost:4200.)*

---

## 🌍 Project Workflow (Example Scenario)

1. A user reports an issue via the interface in the Antalya / Döşemealtı region with the title "Smoke among the trees" and the description "Carries forest fire risk". The user set the urgency of the event to "3 (Medium)".
2. When the form reaches the Backend, it is recorded in MySql and the Frontend instantly displays it on the map.
3. In the same second, the Backend passes the report data to the AI Service in JSON format.
4. The Classifier agent in the AI service uses the `DistrictRiskTool` and determines that Döşemealtı carries a high forest fire risk. Even if the user selected urgency "3", the agent system intervenes and raises this to the "5 (Critical)" level.
5. The Planner agent examines the report and leaves an operational note, directly assigning the responsibility to the "Antalya Fire Department".
6. This decision made by the agents returns to the Backend, and the database is updated.
7. The Backend sends a trigger to the WebSocket, and the open Dashboard screen of operators autonomously evolves into "Smoke - P5 - Fire Department" without needing a page refresh.

---

_This project aims to bring a fully-equipped modern and AI-based vision to complex smart city needs._
