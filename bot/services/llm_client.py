"""LLM client for intent recognition.

This module provides a client for interacting with the LLM API
to understand user intent and route to appropriate tools.
"""

import httpx
import json
from typing import Optional, List, Dict, Any, Callable

from config import settings


# Define 9 available tools for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_health",
            "description": "Check if the backend is healthy and get the number of items in the database. Use this when the user asks about system status, if the backend is working, health check, or server status.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_labs",
            "description": "Get a list of all available labs. Use this when the user asks about available labs, what labs exist, wants to see the lab list, or asks which labs are available.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get scores and pass rates for a specific lab. Use this when the user asks about scores, pass rates, statistics, or performance for a specific lab. Requires a lab identifier like 'lab-01', 'lab-04', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier in format 'lab-XX' where XX is a 2-digit number (e.g., 'lab-01', 'lab-04', 'lab-07'). Extract the lab number from the user's query and format it as 'lab-XX'."
                    }
                },
                "required": ["lab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_help",
            "description": "Get a list of available commands. Use this when the user asks for help, what commands are available, how to use the bot, or needs assistance.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sync_data",
            "description": "Trigger the ETL pipeline to sync data from the autochecker API. Use this when the user asks to sync data, refresh data, update the database, run the pipeline, or populate the database.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get all items (labs and tasks) from the database. Use this when the user asks about all items, wants to see the full list of content, or asks what content is available.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_timeline",
            "description": "Get the submissions timeline analytics showing when students submitted their work. Use this when the user asks about submission timeline, when students submitted, or activity over time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_groups",
            "description": "Get group performance analytics comparing different student groups. Use this when the user asks about group performance, compare groups, or how different groups are doing.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get the overall completion rate for the course or a specific lab. Use this when the user asks about completion rate, how many students completed, or overall progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Optional lab identifier (e.g., 'lab-01'). If not provided, returns overall completion rate."
                    }
                },
                "required": []
            }
        }
    },
]

SYSTEM_PROMPT = """You are an assistant that helps users interact with an LMS (Learning Management System) via a Telegram bot.

You have access to the following tools:
1. get_health - Check backend health and item count
2. get_labs - List all available labs
3. get_scores - Get scores/pass rates for a specific lab (requires lab identifier in format 'lab-XX')
4. get_help - List available commands
5. sync_data - Trigger ETL pipeline to sync data from autochecker API
6. get_items - Get all items (labs and tasks) from database
7. get_analytics_timeline - Get submissions timeline analytics
8. get_analytics_groups - Get group performance analytics
9. get_completion_rate - Get completion rate for course or specific lab

When the user asks a question, determine which tool to call based on their intent:
- System status, health, backend working → get_health
- Available labs, what labs exist → get_labs
- Scores, pass rates, statistics for a lab → get_scores with lab identifier
- Help, commands, how to use → get_help
- Sync data, refresh, update database, run pipeline → sync_data
- All items, full content list → get_items
- Submission timeline, when students submitted → get_analytics_timeline
- Group performance, compare groups → get_analytics_groups
- Completion rate, how many completed → get_completion_rate

For lab identifiers, extract the number from the query and format as 'lab-XX' (e.g., "lab 04" → "lab-04", "lab-01" → "lab-01").

Respond with ONLY a JSON object in this format:
{"tool": "tool_name", "arguments": {"arg1": "value1"}}

If no tool matches or you're unsure, respond with: {"tool": null, "response": "I'm not sure how to help with that. Use /help to see available commands."}
"""


class LLMClient:
    """Client for the LLM API (Qwen Code)."""

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_api_base_url
        self.model = settings.llm_api_model
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def determine_intent(self, user_message: str) -> Dict[str, Any]:
        """Determine the user's intent and which tool to call.
        
        Args:
            user_message: The user's message text.
            
        Returns:
            Dict with 'tool' name and 'arguments' dict.
        """
        try:
            client = await self.get_client()
            
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 250
                }
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse the JSON response
            try:
                intent = json.loads(content)
                return intent
            except json.JSONDecodeError:
                # If LLM didn't return valid JSON, try to extract it
                import re
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    try:
                        intent = json.loads(json_match.group())
                        return intent
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: return null tool
                return {"tool": None, "response": "I'm not sure how to help with that. Use /help to see available commands."}
                
        except Exception as e:
            return {"tool": None, "response": f"Error connecting to LLM: {str(e)}"}


# Global client instance
llm_client = LLMClient()
