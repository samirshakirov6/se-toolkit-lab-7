"""Intent router for natural language queries.

This module routes user messages to the appropriate handler
based on LLM-determined intent with tool calling loop.
"""

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any

from services.llm_client import llm_client, TOOLS, SYSTEM_PROMPT
from services.lms_api import lms_client
from handlers import (
    handle_health_async,
    handle_labs_async,
    handle_scores_async,
    handle_help,
)


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool and return the result.

    Args:
        tool_name: Name of the tool to execute.
        arguments: Arguments to pass to the tool.

    Returns:
        Tool execution result.
    """
    if tool_name == "get_items" or tool_name == "get_labs":
        items = await lms_client.get_all_items()
        return {"items": items, "count": len(items)}

    elif tool_name == "get_learners":
        learners = await lms_client.get_learners()
        return {"learners": learners, "count": len(learners)}

    elif tool_name == "get_scores":
        lab = arguments.get("lab", "")
        scores = await lms_client.get_scores(lab)
        return {"lab": lab, "scores": scores}

    elif tool_name == "get_pass_rates":
        lab = arguments.get("lab", "")
        pass_rates = await lms_client.get_pass_rates(lab)
        return {"lab": lab, "pass_rates": pass_rates}

    elif tool_name == "get_timeline":
        lab = arguments.get("lab", "")
        timeline = await lms_client.get_timeline(lab)
        return {"lab": lab, "timeline": timeline}

    elif tool_name == "get_groups":
        lab = arguments.get("lab", "")
        groups = await lms_client.get_groups(lab)
        return {"lab": lab, "groups": groups}

    elif tool_name == "get_top_learners":
        lab = arguments.get("lab", "")
        limit = arguments.get("limit", 10)
        top_learners = await lms_client.get_top_learners(lab, limit)
        return {"lab": lab, "limit": limit, "top_learners": top_learners}

    elif tool_name == "get_completion_rate":
        lab = arguments.get("lab", "")
        result = await lms_client.get_completion_rate(lab)
        return {"lab": lab, "completion_rate": result}

    elif tool_name == "trigger_sync":
        result = await lms_client.sync_data()
        return {"sync_result": result}

    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def route_intent_async(message: str) -> str:
    """Route a natural language message to the appropriate handler (async).

    Uses a tool-calling loop: LLM decides which tool to call, we execute it,
    feed results back to LLM, and repeat until LLM produces final answer.

    Args:
        message: The user's message text.

    Returns:
        Response text to send to the user.
    """
    # Build conversation history
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ]

    max_iterations = 5  # Prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Call LLM to get next action
        try:
            client = await llm_client.get_client()
            response = await client.post(
                "/chat/completions",
                json={
                    "model": llm_client.model,
                    "messages": messages,
                    "tools": TOOLS,
                    "tool_choice": "auto",
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"

        assistant_message = result["choices"][0]["message"]

        # Check if LLM wants to call tools
        tool_calls = assistant_message.get("tool_calls", [])

        if not tool_calls:
            # LLM produced final answer
            final_content = assistant_message.get("content", "")
            if final_content:
                # Try to parse JSON response from LLM
                try:
                    response_data = json.loads(final_content)
                    if isinstance(response_data, dict):
                        # If LLM returned {"tool": null, "response": "..."}, extract response
                        return response_data.get("response", final_content)
                except json.JSONDecodeError:
                    pass
                return final_content
            else:
                return "I'm not sure how to help with that. Use /help to see available commands."

        # Add assistant message with tool calls to history
        messages.append(assistant_message)

        # Execute each tool call
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            tool_name = function.get("name", "")
            tool_args_str = function.get("arguments", "{}")

            try:
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                tool_args = {}

            print(f"[tool] LLM called: {tool_name}({tool_args})", file=sys.stderr)

            # Execute the tool
            tool_result = await execute_tool(tool_name, tool_args)

            print(f"[tool] Result: {json.dumps(tool_result, default=str)[:200]}...", file=sys.stderr)

            # Add tool result to conversation as user message (Qwen compatibility)
            messages.append({
                "role": "user",
                "content": f"Tool result for {tool_name}: {json.dumps(tool_result, default=str)}"
            })

        print(f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM", file=sys.stderr)

    # If we reach here, max iterations exceeded
    return "This query requires too many steps. Please try a more specific question."


def process_natural_language(message: str) -> str:
    """Process a natural language message (sync wrapper for --test mode).

    Args:
        message: The user's message text (without leading /).

    Returns:
        Response text to send to the user.
    """
    try:
        loop = asyncio.get_running_loop()
        future = asyncio.ensure_future(route_intent_async(message))
        return loop.run_until_complete(future)
    except RuntimeError:
        return asyncio.run(route_intent_async(message))
