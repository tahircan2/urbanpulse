"""
urbanpulse.langgraph_pipeline.nodes.utils — Shared node utilities.

Contains helper logic for tool execution loops, LLM interaction patterns,
and MCP-aware tool resolution with structured logging.
"""
from __future__ import annotations

import json
from typing import List, Any

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from urbanpulse.core.config import get_settings
from urbanpulse.core.logging import get_logger

logger = get_logger(__name__)

def get_llm(temperature: float = 0.0, max_tokens: int = 1024) -> ChatOpenAI:
    """Create and return a configured ChatOpenAI instance."""
    s = get_settings()
    return ChatOpenAI(
        model=s.langgraph_model,
        api_key=s.openai_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_active_tool_list() -> tuple[list, str]:
    """
    Resolve active tools using the dual-mode system.

    Returns:
        Tuple of (tool_list, mode) where mode is 'mcp' or 'direct'.
    """
    from urbanpulse.langgraph_pipeline.tools import get_active_tools
    s = get_settings()
    return get_active_tools(prefer_mcp=s.mcp_enabled)


def invoke_with_tools(
    llm: ChatOpenAI,
    messages: List[BaseMessage],
    tools: List[Any],
    max_rounds: int = 2
) -> str:
    """
    Execute an LLM loop that allows for tool calling before returning final text.

    This function supports both direct LangChain tools and MCP-adapted tools.
    It logs every tool call with its source (MCP or direct) for observability.

    Strictly adheres to the max_rounds setting to prevent infinite loops.
    """
    # Determine the active mode for logging context
    _active_mode = "unknown"
    try:
        _, _active_mode = get_active_tool_list()
    except Exception:
        pass

    llm_with_tools = llm.bind_tools(tools)
    
    current_messages = messages.copy()
    rounds = 0
    
    logger.info(
        "tool_loop_start",
        mode=_active_mode,
        max_rounds=max_rounds,
        available_tools=[t.name for t in tools],
    )

    while rounds < max_rounds:
        res = llm_with_tools.invoke(current_messages)
        current_messages.append(res)
        
        if not res.tool_calls:
            logger.info(
                "tool_loop_end",
                mode=_active_mode,
                rounds_used=rounds,
                reason="no_more_tool_calls",
            )
            return res.content
        
        # Execute tool calls
        for tool_call in res.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            logger.info(
                "tool_call_dispatch",
                mode=_active_mode,
                tool=tool_name,
                arguments=tool_args,
                round=rounds + 1,
            )

            # Find the tool in our list
            selected_tool = next((t for t in tools if t.name == tool_name), None)
            if not selected_tool:
                result = f"Error: Tool {tool_name} not found."
                logger.error("tool_not_found", tool=tool_name, mode=_active_mode)
            else:
                try:
                    result = selected_tool.run(tool_args)
                    logger.info(
                        "tool_call_result",
                        mode=_active_mode,
                        tool=tool_name,
                        result_preview=str(result)[:150],
                    )
                except Exception as e:
                    result = f"Error executing {tool_name}: {str(e)}"
                    logger.error(
                        "tool_call_error",
                        mode=_active_mode,
                        tool=tool_name,
                        error=str(e),
                    )
            
            current_messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=str(result)
                )
            )
        
        rounds += 1
        logger.debug(
            "tool_loop_round_complete",
            mode=_active_mode,
            round=rounds,
            tool_calls_count=len(res.tool_calls),
        )
    
    logger.info(
        "tool_loop_end",
        mode=_active_mode,
        rounds_used=rounds,
        reason="max_rounds_reached",
    )

    # If we hit max rounds, try one last time without tools to get final answer
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
