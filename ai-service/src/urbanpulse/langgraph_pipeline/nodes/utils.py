"""
urbanpulse.langgraph_pipeline.nodes.utils — Shared node utilities.

Contains helper logic for tool execution loops and standard LLM interaction patterns.
"""
from __future__ import annotations

import json
from typing import List, Any

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from urbanpulse.core.config import get_settings
from urbanpulse.core.logging import get_logger

logger = get_logger(__name__)


def invoke_with_tools(
    llm: ChatOpenAI,
    messages: List[BaseMessage],
    tools: List[Any],
    max_rounds: int = 2
) -> str:
    """
    Execute an LLM loop that allows for tool calling before returning final text.
    Strictly adheres to the max_rounds setting to prevent infinite loops.
    """
    llm_with_tools = llm.bind_tools(tools)
    
    current_messages = messages.copy()
    rounds = 0
    
    while rounds < max_rounds:
        res = llm_with_tools.invoke(current_messages)
        current_messages.append(res)
        
        if not res.tool_calls:
            return res.content
        
        # Execute tool calls
        for tool_call in res.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find the tool in our list
            selected_tool = next((t for t in tools if t.name == tool_name), None)
            if not selected_tool:
                # This shouldn't happen if LLM is well-behaved
                result = f"Error: Tool {tool_name} not found."
            else:
                try:
                    result = selected_tool.run(tool_args)
                except Exception as e:
                    result = f"Error executing {tool_name}: {str(e)}"
            
            current_messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=str(result)
                )
            )
        
        rounds += 1
        logger.debug("tool_loop_round", round=rounds, tool_calls_count=len(res.tool_calls))
    
    # If we hit max rounds, just return the last content or instruct to wrap up
    # We'll try one last time without tools to get a summary if it's still stuck
    if any(m.type == "ai" and getattr(m, "tool_calls", None) for m in current_messages):
        final_res = llm.invoke(current_messages + [HumanMessage(content="Tools execution finished. Provide your final JSON response now.")])
        return final_res.content
        
    return res.content


def parse_llm_json(content: str) -> dict:
    """Robustly extract JSON from LLM output."""
    try:
        clean = content.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)
    except Exception:
        s, e = content.find("{"), content.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(content[s:e])
            except Exception:
                pass
        return {}
