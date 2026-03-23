#!/usr/bin/env python3
"""Test LLM intent extraction."""

import asyncio
from services.llm_client import llm_client

async def test(message):
    result = await llm_client.determine_intent(message)
    print(f"Query: {message!r}")
    print(f"Result: {result}")
    print()

asyncio.run(test("show me scores for lab 04"))
asyncio.run(test("scores for lab-04"))
asyncio.run(test("what are the scores for lab 4"))
