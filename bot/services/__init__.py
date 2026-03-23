"""Services for the LMS Telegram bot.

This module contains service classes for external API interactions:
- LMS API client for fetching data from the backend
- LLM client for intent recognition (Task 3)
"""

from services.lms_api import LMSAPIClient, lms_client
from services.llm_client import LLMClient, llm_client

__all__ = ["LMSAPIClient", "lms_client", "LLMClient", "llm_client"]
