#!/usr/bin/env python3
"""Test LLM client."""

import asyncio
from services.llm_client import llm_client

print("API Key:", llm_client.api_key)
print("Base URL:", llm_client.base_url)
print("Model:", llm_client.model)

async def test():
    result = await llm_client.determine_intent("what labs are available")
    print("Result:", result)

asyncio.run(test())
