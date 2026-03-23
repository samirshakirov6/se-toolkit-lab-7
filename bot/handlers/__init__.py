"""Command handlers for the LMS Telegram bot.

This module contains handler functions that process commands
and return text responses. Handlers are independent of Telegram
and can be tested via --test mode or unit tests.
"""

import asyncio
import re
from typing import Optional

from services.lms_api import lms_client


def handle_start() -> str:
    """Handle /start command.
    
    Returns:
        Welcome message string.
    """
    return "Welcome to the LMS Bot! Use /help to see available commands."


def handle_help() -> str:
    """Handle /help command.
    
    Returns:
        List of available commands.
    """
    return (
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - Get scores for a lab"
    )


def handle_health() -> str:
    """Handle /health command (sync version).
    
    Returns:
        Backend status message with items count.
    """
    try:
        loop = asyncio.get_running_loop()
        result = loop.run_until_complete(lms_client.health_check())
    except RuntimeError:
        result = asyncio.run(lms_client.health_check())
    
    if result["status"] == "up":
        items_count = result.get("items_count", 0)
        return f"✅ Backend is UP and running with {items_count} items in database"
    else:
        return f"❌ Backend is DOWN: {result['details']}"


async def handle_health_async() -> str:
    """Handle /health command (async version).
    
    Returns:
        Backend status message with items count.
    """
    result = await lms_client.health_check()
    if result["status"] == "up":
        items_count = result.get("items_count", 0)
        return f"✅ Backend is UP and running with {items_count} items in database"
    else:
        return f"❌ Backend is DOWN: {result['details']}"


def handle_labs() -> str:
    """Handle /labs command (sync version).
    
    Returns:
        List of available labs.
    """
    try:
        loop = asyncio.get_running_loop()
        labs = loop.run_until_complete(lms_client.get_labs())
    except RuntimeError:
        labs = asyncio.run(lms_client.get_labs())
    
    if not labs:
        return "No labs available or backend is unreachable"
    
    response = "📚 Available Labs:\n\n"
    for lab in labs:
        lab_id = lab.get("id", "?")
        title = lab.get("title", "Unknown")
        response += f"• **Lab {lab_id}**: {title}\n"
    
    return response


async def handle_labs_async() -> str:
    """Handle /labs command (async version).
    
    Returns:
        List of available labs.
    """
    labs = await lms_client.get_labs()
    
    if not labs:
        return "No labs available or backend is unreachable"
    
    response = "📚 Available Labs:\n\n"
    for lab in labs:
        lab_id = lab.get("id", "?")
        title = lab.get("title", "Unknown")
        response += f"• **Lab {lab_id}**: {title}\n"
    
    return response


def handle_scores(lab_query: Optional[str] = None) -> str:
    """Handle /scores command (sync version).
    
    Args:
        lab_query: Lab name or ID to get scores for.
        
    Returns:
        Scores information for the specified lab.
    """
    try:
        loop = asyncio.get_running_loop()
        return _handle_scores_async_impl(lab_query, loop)
    except RuntimeError:
        return asyncio.run(_handle_scores_async_impl(lab_query, None))


async def handle_scores_async(lab_query: Optional[str] = None) -> str:
    """Handle /scores command (async version).
    
    Args:
        lab_query: Lab name or ID to get scores for.
        
    Returns:
        Scores information for the specified lab.
    """
    return await _handle_scores_async_impl(lab_query, None)


async def _handle_scores_async_impl(lab_query: Optional[str], loop) -> str:
    """Internal implementation for /scores handler."""
    if not lab_query:
        return "Please specify a lab name, e.g., /scores lab-01 or /scores 1"
    
    # Lab identifier should come from LLM in lab-XX format
    # Just normalize it: extract number and format as lab-XX
    lab_identifier = None
    lab_title = None
    
    # Extract lab number from query (e.g., "lab-04" -> "04", "lab 04" -> "04", "4" -> "04")
    import re
    # Try to find any number in the query
    numbers = re.findall(r'\d+', lab_query)
    if numbers:
        # Take the first number found
        lab_num = numbers[0].zfill(2)
        lab_identifier = f"lab-{lab_num}"
    
    if not lab_identifier:
        return f"Lab '{lab_query}' not found. Use /labs to see available labs."
    
    # Find lab title for display
    if loop:
        labs = loop.run_until_complete(lms_client.get_labs())
    else:
        labs = await lms_client.get_labs()
    for lab in labs:
        title = lab.get("title", "")
        if lab_identifier.replace("lab-", "") in title or lab_identifier in title.lower():
            lab_title = title
            break
    if not lab_title:
        lab_title = f"Lab {lab_identifier.replace('lab-', '')}"
    
    # Get pass rates for the lab
    if loop:
        pass_rates = loop.run_until_complete(lms_client.get_pass_rates(lab_identifier))
    else:
        pass_rates = await lms_client.get_pass_rates(lab_identifier)
    
    if not pass_rates:
        # No pass rates - show submission stats instead
        if loop:
            scores_data = loop.run_until_complete(lms_client.get_scores(lab_identifier))
        else:
            scores_data = await lms_client.get_scores(lab_identifier)
        if scores_data and "scores" in scores_data:
            scores = scores_data["scores"]
            response = f"📊 {lab_title}\n\n"
            response += "Score distribution:\n"
            total_submissions = 0
            for bucket in scores:
                bucket_name = bucket.get("bucket", "?")
                count = bucket.get("count", 0)
                total_submissions += count
                response += f"  • {bucket_name}: {count} submissions\n"
            response += f"\nTotal: {total_submissions} attempts"
            return response
        
        return f"📊 {lab_title}\n\nNo score data available yet."
    
    # Format pass rates response
    response = f"📊 {lab_title}\n\n"
    response += "Pass rates by task:\n"
    
    total_score = 0
    total_attempts = 0
    for task in pass_rates:
        # API returns 'task' and 'avg_score', not 'task_title' and 'pass_rate'
        task_name = task.get("task", task.get("task_title", "Unknown"))
        # Use avg_score if available, otherwise pass_rate
        score = task.get("avg_score", task.get("pass_rate", 0))
        submissions = task.get("attempts", task.get("submissions", 0))
        total_score += score
        total_attempts += submissions
        response += f"  • {task_name}: {score:.1f}% ({submissions} attempts)\n"
    
    # Add average score
    if pass_rates:
        avg_score = total_score / len(pass_rates)
        response += f"\nAverage: {avg_score:.1f}% score across {total_attempts} total attempts"
    
    return response


def handle_unknown(command: str) -> str:
    """Handle unknown commands.
    
    Args:
        command: The unknown command string.
        
    Returns:
        Error message suggesting to use /help.
    """
    return f"Unknown command: {command}. Use /help to see available commands."
