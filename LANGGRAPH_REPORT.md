# LangGraph Integration into UrbanPulse AI Service

## 1. Executive Summary
This report details the integration of LangGraph into the UrbanPulse AI service alongside the pre-existing CrewAI setup. Both pipelines exist independently. The LangGraph setup handles incident classification, response planning, generation of summaries, and enforces safety guardrails via explicit state transitions, providing deterministic control compared to a free-form multi-agent setup.

## 2. Architecture & Integration
The state transitions represent a rigid flow from start to completion:
`input_guard \u2192 classify \u2192 plan \u2192 monitor \u2192 output_guard`
If `input_guard` detects malicious intent, the flow routes strictly to `rejected` without wasting LLM cycles or exposing the system.

A new FastAPI router exposes `/api/langgraph/process` to handle requests with the standard `IncidentDTO` format, seamlessly returning a `PipelineResult` consistent with the CrewAI output.

## 3. LangGraph State Schema
The explicit `PipelineState` tracks everything cleanly: data input, classifier values, planner selections, monitoring blurbs, tool calling tracks, and guardrail decisions in a typed dictionary.

## 4. LangSmith Integration
LangSmith tracing is fully functional, instantiated during the application lifespan and driven entirely by environment variables in `.env` and `docker-compose.yml`.

## 5. Comparison: CrewAI vs LangGraph
While CrewAI provides simple 'goal-oriented' agent declarations (classifier, planner, monitor), LangGraph ensures each logical step and tool invocation runs in distinct isolated functions matching graph edges. This adds control, prevents unexpected cyclic behaviors, and is significantly lighter in dependencies.

## 6. How to run & test
Start the system as normal via Docker. Ping `/api/health` to confirm the `LANGGRAPH` agent appears in the list. POST requests directly to `/api/langgraph/process`.
