# CrewAI Implementation Report: UrbanPulse

## 1. Executive Summary
**UrbanPulse** is an AI-driven incident management platform designed for the Antalya Büyükşehir Belediyesi. The core "intelligence" of the system is powered by a **CrewAI multi-agent pipeline**. This pipeline automates the classification, prioritization, and response planning of city incidents (e.g., fires, floods, traffic accidents) reported by citizens.

By integrating CrewAI, the system moves beyond simple data entry into autonomous decision-making, ensuring that life-critical incidents are identified and routed to the correct municipal departments with mathematically calculated SLAs.

---

## 2. System Architecture & Integration (Homework 2)
This project is an evolution of a full-stack Spring Boot (Backend) and Angular (Frontend) application. The CrewAI service is implemented as a dedicated **FastAPI microservice** that communicates with the Java backend via REST API callbacks and WebSockets.

- **Frontend (Angular):** Captures user reports and displays real-time agent "thoughts" and logs.
- **Backend (Spring Boot):** Handles persistence and triggers the AI pipeline asynchronously.
- **AI Service (CrewAI):** Processes the incident using a 3-agent crew.

---

## 3. Agent Definitions (agents.yaml)
The system utilizes three specialized agents defined in a configuration file. Our strategy uses **Role-Based Agent Design** to ensure high-quality outputs.

### [Classifier Agent]
- **Role:** Antalya Smart City Incident Classifier
- **Goal:** Accurately classify category and priority, overriding user input if necessary.
- **Backstory:** Expert in Mediterranean climate hazards and regional emergency protocols.

### [Planner Agent]
- **Role:** Antalya Büyükşehir Belediyesi Incident Response Planner
- **Goal:** Assign the correct department and calculate a realistic SLA.
- **Backstory:** Senior operations coordinator with 15 years of experience in routing incidents.

### [Monitor Agent]
- **Role:** UrbanPulse Pipeline Monitor
- **Goal:** Summarize the decision into a concise audit trail.

---

## 4. Task Definitions (tasks.yaml)
Tasks are designed using **Sequential Logic**, where the output of the Classifier is passed as context to the Planner.

### Task: `classify_incident`
- **Description:** Classify the incident by checking district risk profiles, seasonal context (tourist vs non-tourist), and weather data. Priority must be escalated for life-threatening descriptions.
- **Agent:** Classifier

### Task: `plan_response`
- **Description:** Route to departments like ASAT (Water) or AEDAŞ (Electric). Calculate SLA based on: `base_sla * priority_multiplier * time_multiplier`.
- **Agent:** Planner
- **Context:** [classify_incident]

---

## 5. Core Implementation (crew.py)
The following Python code initializes the Crew using the memory and cache features of the CrewAI framework.

```python
@CrewBase
class Urbanpulse():
    """Urbanpulse crew for Antalya City Incident Management"""

    @agent
    def classifier(self) -> Agent:
        return Agent(config=self.agents_config['classifier'], tools=[risk_tool, weather_tool])

    @agent
    def planner(self) -> Agent:
        return Agent(config=self.agents_config['planner'], tools=[pattern_tool])

    @task
    def classify_incident(self) -> Task:
        return Task(config=self.tasks_config['classify_incident'])

    @task
    def plan_response(self) -> Task:
        return Task(config=self.tasks_config['plan_response'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
```

---

## 6. Kickoff & Execution Logic
The pipeline is triggered via a FastAPI endpoint. We use the `kickoff()` method to start the process with dynamic parameters from the database.

```python
@router.post("/process")
async def process_incident(payload: dict):
    # Inputs are extracted from the request
    inputs = payload.get("incident", {})
    
    # Initialize the crew and kickoff
    result = Urbanpulse().crew().kickoff(inputs=inputs)
    
    return {"status": "success", "raw_output": result.raw}
```

---

## 7. Conclusion
This CrewAI implementation successfully adds an autonomous layer to the UrbanPulse project. By leveraging multi-agent collaboration, the system can detect "systemic issues" (recurring patterns) and override human errors in reporting, significantly improving the reliability of city-wide emergency management.


---

## 8. Visual Demonstration: AI Pipeline Dashboard


**Technical Explanation of the UI:**
The screenshot above demonstrates the live integration of the **CrewAI pipeline** within the UrbanPulse Command Center. Unlike a static script, this implementation provides a reactive user experience:
- **Agent Transparency:** The UI displays three distinct cards (Classifier, Planner, Monitor). Each card shows the agent's internal reasoning and output.
- **State Synchronization:** The progress bars and "thoughts" shown in the UI are synchronized with the Python service via **WebSockets**.
- **Data Persistence:** This view confirms that the CrewAI outputs (category, priority) have been successfully saved to the SQL database via the Spring Boot API.

---

## 9. Technical Note: Map vs. Pipeline Views
You may notice minor differences between the "Live Map" and the "AI Pipeline" tab. This is intentional:
1. **Localization:** The Map/Table uses **Turkish labels** (e.g., 'Yangın Tehlikesi') for city staff, while the Pipeline shows **raw English AI output** (e.g., 'FIRE_HAZARD') for audit purposes.
2. **Granularity:** The Pipeline shows the **internal reasoning** of all agents, whereas the Map displays only the **final consolidated result** and the Monitor's summary.
3. **Processing State:** The Map initially shows user-reported data until the AI process completes (indicated by the green checkmark), at which point it updates to the AI-validated values.
