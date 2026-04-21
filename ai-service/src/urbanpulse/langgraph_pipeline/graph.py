"""
urbanpulse.langgraph_pipeline.graph — Graph construction & compilation.

Imports nodes and wires them into a LangGraph StateGraph.
This module is intentionally thin — node logic lives in nodes/.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from urbanpulse.langgraph_pipeline.state import PipelineState
from urbanpulse.langgraph_pipeline.nodes import (
    classify_node,
    plan_node,
    monitor_node,
    rejected_node,
    input_guard_node,
    output_guard_node,
    route_after_guard,
)


# ── Graph Assembly ────────────────────────────────────────────────────────────

graph = StateGraph(PipelineState)

# Add nodes
graph.add_node("input_guard",  input_guard_node)
graph.add_node("classify",     classify_node)
graph.add_node("plan",         plan_node)
graph.add_node("monitor",      monitor_node)
graph.add_node("output_guard", output_guard_node)
graph.add_node("rejected",     rejected_node)

# Wire edges
graph.set_entry_point("input_guard")
graph.add_conditional_edges("input_guard", route_after_guard, {
    "classify": "classify",
    "rejected": "rejected",
})
graph.add_edge("classify", "plan")
graph.add_edge("plan", "monitor")
graph.add_edge("monitor", "output_guard")
graph.add_edge("output_guard", END)
graph.add_edge("rejected", END)

# Compile
compiled_graph = graph.compile()
