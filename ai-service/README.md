# UrbanPulse AI Service 🧠

This folder (`ai-service`) forms the artificial intelligence brain of the UrbanPulse project. Emergency and incident reports coming from the city (Antalya) pass through an autonomous agent pipeline utilizing the **CrewAI** infrastructure. This pipeline consists of completely independent yet collaborative agents.

This document is prepared to explain how the system works 100% transparently, the CrewAI architecture, and the decision-making processes of the agents from scratch.

---

## 1. System Logic (Overview)

When a citizen submits a report via the Frontend (Angular), the request first reaches the Backend (Spring Boot). The Backend saves the report and then sends a `POST /api/pipeline/process` request to this Python (FastAPI) service.

When the request arrives here, a classic software function does not run; instead, an agent team (Crew) named **UrbanPulseCrew** awakens. The report information is handed over to this autonomous team. The task distribution among the files is as follows:
- `main.py` & `routes/pipeline.py`: The FastAPI server and the API endpoint communicating with Spring Boot.
- `crew.py`: The file where the CrewAI team (Agents + Tasks) is coded, acting as the team's manager.
- `config/agents.yaml`: The identities, roles, and backstories of the agents.
- `config/tasks.yaml`: What the agents will concretely do and what output they will produce.
- `tools/`: The "digital toolbox" given to the agents so they can fetch data from the outside world.

---

## 2. What is CrewAI and How Does It Work?

**CrewAI** is a framework that transforms artificial intelligence models (LLMs) into "agents". It does this by giving each agent a "Role", a "Goal", and a "Backstory".

In the UrbanPulse project, a **3-stage (Sequential) Pipeline** runs. This means the agents run in order, and when one finishes its task, it hands over its generated result to the next:
`Classifier ➔ Planner ➔ Monitor`

### Step by Step Operation

#### A) Guardrail (Security Pre-Check)
Before the agents awaken, `validator.py` kicks in. It quickly checks if there is any inconsistency between the title and the description of the incoming report (For example: Title is "Fire" but description is "Cat stuck in a tree"). We provide the resulting outcome to the agents as preliminary information (consistency_warning).

#### B) Stage 1: Classifier (Classifier Agent)
- **Mission:** To never blindly accept the category or urgency level entered by the citizen; to find the truth.
- **How It Works:** When it receives the report, it looks at the rules in `tasks.yaml`. If there is an urgent word like "Fire", it immediately pulls the priority to P5.
- **Tools Used:** 
  - `Risk Profile Tool`: Quickly determines if the mentioned district has a forest fire or flood risk.
  - `Time Context Tool`: Checks if it's 3 AM or tourism season.
  - `Weather Tool`, `Location Tool` etc...
- **Output:** The finalized, verified Category, Priority (Urgency), and the "Why did I make this decision?" (Reasoning) sentence.

#### C) Stage 2: Planner (Planner Agent)
- **Mission:** To decide which institution (e.g., Antalya Fire Department) will solve the classified report and determine an SLA (Service Level Agreement) timeframe.
- **How It Works:** Inherits the Classifier's result. If it's tourism season (August) and the event is in a touristic area (Kemer), it applies a 0.5x multiplier to keep the SLA duration shorter.
- **Tools Used:**
  - `Similar Incidents Tool`: Have there been similar reports from that area before? If so, it tags this as a "Systemic Issue".
- **Output:** The department name, SLA hour limit, and an operational advice note (Action Note). (E.g.: "Antalya Fire Department, SLA: 1 hour").

#### D) Stage 3: Monitor (Observer Agent)
- **Mission:** To create a summary of the entire process of the incoming report.
- **How It Works:** Sees what both the Classifier and the Planner have done. Combines all this complex data.
- **Output:** Just a single, understandable English sentence. (E.g.: *"P5 FIRE_HAZARD routed to Antalya Fire Department with 1h SLA."*)

---

## 3. Tools (Toolbox) Architecture
Agents are not naturally connected to the internet or the real world. We give them Python scripts we wrote ourselves (with the `@tool` decorator). UrbanPulse tools (`src/urbanpulse/tools/*`):

1. **`DistrictRiskTool`**: Holds the risk database of districts in Antalya. When the agent queries the district, it learns if there is a forest fire or flood risk.
2. **`TimeContextTool`**: Calculates data such as whether it's a workday, weekend, or working hours.
3. **`WeatherTool`**: If necessary, the agent uses this to forecast the weather.
4. **`InfrastructureTool`**: Checks if there are critical centers like hospitals/schools close to the location.
5. **`SimilarIncidentsTool`**: Used to identify a regional chronic problem.

When an agent needs it, it calls the functions of these tools as if using a keyboard with its own hands. It takes the result, reads it, and proceeds step by step towards the target in `tasks.yaml`.

---

## 4. Service Installation 

The project runs on Python 3.12+ with the UV package manager.

```bash
uv venv
uv pip install -r requirements.txt
```

To start:
```bash
python run.py
```
*(This command starts the Uvicorn server on port 8000.)*

## 5. Summary

This AI service gets rid of traditional if-else structures; it is a multi-layered, boundary-defined (validated with `schemas.py`) CrewAI team that classifies reports and routes them to units by thinking flexibly, almost like a conscious operation manager, based on the content, time, and location of the incident (report).
