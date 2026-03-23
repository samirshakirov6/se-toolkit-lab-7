"""LLM client for intent recognition.

This module provides a client for interacting with the LLM API
to understand user intent and route to appropriate tools.
"""

import httpx
import json
from typing import Optional, List, Dict, Any, Callable

from config import settings


# Define 9+ available tools for the LLM (all backend endpoints)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get list of all labs and tasks from the database. Use when user asks: what labs exist, list all items, show available content, what labs are available, get labs list.",
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
            "description": "Get list of all labs (alias for get_items). Use when user asks: what labs exist, list labs, show labs, get labs list.",
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
            "name": "get_learners",
            "description": "Get list of all enrolled students and their groups. Use when user asks: how many students, list learners, who is enrolled, student count, show all students.",
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
            "description": "Get score distribution (4 buckets) for a specific lab. Use when user asks about scores, score distribution, how students performed in a lab. Requires lab parameter like 'lab-01'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier in format 'lab-XX' (e.g., 'lab-01', 'lab-04'). Extract number from query and format as 'lab-XX'."
                    }
                },
                "required": ["lab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a specific lab. Use when user asks: pass rates, average scores, task performance, how hard is a lab, lab statistics. Requires lab parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier in format 'lab-XX' (e.g., 'lab-01', 'lab-04')."
                    }
                },
                "required": ["lab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submissions per day for a lab showing activity over time. Use when user asks: timeline, when students submitted, activity over time, submission dates. Requires lab parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier in format 'lab-XX'."
                    }
                },
                "required": ["lab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group scores and student counts for a lab. Use when user asks: group performance, compare groups, which group is best, group statistics. Requires lab parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier in format 'lab-XX'."
                    }
                },
                "required": ["lab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by score for a lab. Use when user asks: top students, best learners, leaderboard, ranking, who performed best. Requires lab and optional limit (default 10).",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier in format 'lab-XX'."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top learners to return (default 10)."
                    }
                },
                "required": ["lab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a lab. Use when user asks: completion rate, how many completed, what percentage finished, lab completion stats. Requires lab parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier in format 'lab-XX'."
                    }
                },
                "required": ["lab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Refresh data from autochecker by running the ETL pipeline. Use when user asks: sync data, refresh, update database, run pipeline, get latest data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
]

SYSTEM_PROMPT = """You are an assistant that helps users interact with an LMS (Learning Management System) via a Telegram bot.

You have access to 9 tools that map to backend API endpoints:
1. get_items - List all labs and tasks
2. get_learners - List enrolled students and groups
3. get_scores - Score distribution for a lab (requires lab)
4. get_pass_rates - Per-task averages and attempts for a lab (requires lab)
5. get_timeline - Submissions per day for a lab (requires lab)
6. get_groups - Per-group scores for a lab (requires lab)
7. get_top_learners - Top N learners for a lab (requires lab, optional limit)
8. get_completion_rate - Completion rate for a lab (requires lab)
9. trigger_sync - Refresh data from autochecker

IMPORTANT:
- Always extract lab numbers from user queries and format as 'lab-XX' (e.g., "lab 4" -> "lab-04", "lab-01" -> "lab-01")
- For multi-step queries (e.g., "which lab has lowest pass rate"), first call get_items, then call get_pass_rates for each lab, then compare
- The LLM must call tools to get real data - don't make up answers

Examples:
User: "what labs are available?" → {"tool": "get_items", "arguments": {}}
User: "show scores for lab 4" → {"tool": "get_scores", "arguments": {"lab": "lab-04"}}
User: "which lab has lowest pass rate?" → {"tool": "get_items", "arguments": {}} (then will call get_pass_rates for each)
User: "top 5 students in lab 3" → {"tool": "get_top_learners", "arguments": {"lab": "lab-03", "limit": 5}}
User: "compare groups in lab 2" → {"tool": "get_groups", "arguments": {"lab": "lab-02"}}
User: "sync the data" → {"tool": "trigger_sync", "arguments": {}}
User: "how many students enrolled" → {"tool": "get_learners", "arguments": {}}

Respond with ONLY a JSON object: {"tool": "tool_name", "arguments": {...}}
For multi-step queries, respond with the FIRST tool to call.
If unsure or greeting: {"tool": null, "response": "friendly message with capabilities hint"}
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
                # If LLM didn't return valid JSON, return fallback
                return {"tool": None, "response": "I'm not sure how to help with that. Use /help to see available commands."}

        except Exception as e:
            return {"tool": None, "response": f"Error connecting to LLM: {str(e)}"}


# Global client instance
llm_client = LLMClient()
