#!/usr/bin/env python3
"""Test complex LLM queries."""

import asyncio
from services.llm_client import llm_client
from handlers.intent_router import process_natural_language

async def test_intent(message):
    result = await llm_client.determine_intent(message)
    print(f"Query: {message!r}")
    print(f"Intent: {result}")
    print()

async def test_response(message):
    response = process_natural_language(message)
    print(f"Query: {message!r}")
    print(f"Response: {response[:200]}...")
    print()

print("=== Testing Intent Detection ===")
asyncio.run(test_intent("which lab has the lowest pass rate"))
asyncio.run(test_intent("sync the data"))
asyncio.run(test_intent("show me all analytics"))

print("\n=== Testing Full Responses ===")
asyncio.run(test_response("which lab has the lowest pass rate"))
asyncio.run(test_response("sync the data"))
