"""Intent router for natural language queries.

This module routes user messages to the appropriate handler
based on LLM-determined intent.
"""

import asyncio
from typing import Optional

from services.llm_client import llm_client
from handlers import (
    handle_health_async,
    handle_labs_async,
    handle_scores_async,
    handle_help,
)
from services.lms_api import lms_client


async def route_intent_async(message: str) -> str:
    """Route a natural language message to the appropriate handler (async).
    
    Args:
        message: The user's message text.
        
    Returns:
        Response text to send to the user.
    """
    # Determine intent using LLM
    intent = await llm_client.determine_intent(message)
    
    tool = intent.get("tool")
    arguments = intent.get("arguments", {})
    
    if tool is None:
        # LLM couldn't determine intent or returned an error
        return intent.get("response", "I'm not sure how to help with that. Use /help to see available commands.")
    
    # Execute the appropriate tool
    if tool == "get_health":
        return await handle_health_async()
    
    elif tool == "get_labs":
        return await handle_labs_async()
    
    elif tool == "get_scores":
        # LLM may return 'lab' or 'lab_id' - check both
        lab = arguments.get("lab") or arguments.get("lab_id") or ""
        return await handle_scores_async(lab)
    
    elif tool == "get_help":
        return handle_help()
    
    elif tool == "sync_data":
        result = await lms_client.sync_data()
        if "error" in result:
            return f"Sync failed: {result['error']}"
        new_records = result.get("new_records", 0)
        total_records = result.get("total_records", 0)
        return f"✅ Sync complete! Loaded {new_records} new records ({total_records} total)"
    
    elif tool == "get_items":
        items = await lms_client.get_all_items()
        if not items:
            return "No items found or backend is unreachable"
        labs_count = sum(1 for i in items if i.get("type") == "lab")
        tasks_count = sum(1 for i in items if i.get("type") == "task")
        return f"📦 Total items: {len(items)}\n• Labs: {labs_count}\n• Tasks: {tasks_count}"
    
    elif tool == "get_analytics_timeline":
        timeline = await lms_client.get_analytics_timeline()
        if not timeline:
            return "No timeline data available"
        return f"📈 Submissions timeline: {len(timeline)} data points available"
    
    elif tool == "get_analytics_groups":
        groups = await lms_client.get_analytics_groups()
        if not groups:
            return "No group data available"
        response = "👥 Group Performance:\n\n"
        for group in groups[:5]:  # Show top 5
            name = group.get("group", "Unknown")
            avg = group.get("avg_score", 0)
            response += f"• {name}: {avg:.1f}%\n"
        return response
    
    elif tool == "get_completion_rate":
        lab = arguments.get("lab")
        result = await lms_client.get_completion_rate(lab)
        if not result:
            return "No completion rate data available"
        rate = result.get("completion_rate", 0)
        total = result.get("total_learners", 0)
        completed = result.get("completed_learners", 0)
        return f"📊 Completion Rate: {rate:.1f}%\n{completed}/{total} learners completed"
    
    else:
        return f"Unknown tool: {tool}. Use /help to see available commands."


def process_natural_language(message: str) -> str:
    """Process a natural language message (sync wrapper for --test mode).
    
    Args:
        message: The user's message text (without leading /).
        
    Returns:
        Response text to send to the user.
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in a running loop, use create_task
        future = asyncio.ensure_future(route_intent_async(message))
        return loop.run_until_complete(future)
    except RuntimeError:
        # No running loop, use asyncio.run
        return asyncio.run(route_intent_async(message))
