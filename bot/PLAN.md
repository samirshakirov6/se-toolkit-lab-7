# LMS Telegram Bot — Development Plan

## Overview

This document describes the development plan for building a Telegram bot that lets users interact with the LMS backend through chat. The bot supports slash commands like `/start`, `/help`, `/health`, `/labs`, `/scores`, and can understand plain language questions using an LLM for intent routing.

## Architecture

The bot follows a **layered architecture** with separation of concerns:

1. **Entry Point (`bot.py`)** — Handles Telegram startup and `--test` mode. Routes incoming messages to appropriate handlers.

2. **Handlers (`handlers/`)** — Pure functions that process commands and return text responses. They have no dependency on Telegram, making them testable via `--test` mode and unit tests.

3. **Services (`services/`)** — External API clients:
   - `lms_api.py` — HTTP client for the LMS backend (fetches labs, scores, health status)
   - `llm_client.py` — LLM client for intent recognition (Task 3)

4. **Configuration (`config.py`)** — Loads environment variables from `.env.bot.secret` using pydantic-settings.

## Task 1: Scaffold (Current)

**Goal:** Create project structure and test mode.

- [x] Create `bot/` directory with `pyproject.toml`
- [x] Create `config.py` for environment loading
- [x] Create `bot.py` with `--test` mode
- [x] Create `handlers/` module with placeholder handlers
- [x] Create `services/` module (empty for now)
- [x] Create `.env.bot.example` and `.env.bot.secret`

**Test mode:** `uv run bot.py --test "/start"` prints response to stdout.

## Task 2: Backend Integration

**Goal:** Connect handlers to the LMS backend API.

- [ ] Create `services/lms_api.py` with HTTP client
- [ ] Implement `/health` — call `GET /` or `/items` to check backend status
- [ ] Implement `/labs` — call `GET /items/` and filter labs
- [ ] Implement `/scores <lab>` — call analytics endpoint for pass rates
- [ ] Add error handling for network failures
- [ ] Update handlers to use services instead of placeholders

**Verification:** All commands return real data from the backend.

## Task 3: Intent-Based Natural Language Routing

**Goal:** Enable plain language queries via LLM tool use.

- [ ] Create `services/llm_client.py` for LLM API calls
- [ ] Define tool descriptions for all 9 backend endpoints
- [ ] Implement intent router that asks LLM which tool to call
- [ ] Add system prompt explaining tool usage
- [ ] Handle multi-step reasoning (LLM chains multiple API calls)
- [ ] Add inline keyboard buttons for common actions

**Verification:** Bot understands queries like "what labs are available?" and "show me scores for lab 04".

## Task 4: Containerize and Document

**Goal:** Deploy bot with Docker and document the process.

- [ ] Create `bot/Dockerfile`
- [ ] Add bot service to `docker-compose.yml`
- [ ] Configure networking between bot and backend containers
- [ ] Deploy to VM and verify
- [ ] Update README with deployment instructions
- [ ] Write troubleshooting guide

**Verification:** Bot runs in Docker and responds in Telegram.

## Testing Strategy

1. **Test Mode:** All commands work via `--test` flag without Telegram connection.
2. **Unit Tests:** Handler functions can be tested in isolation.
3. **Integration Tests:** Services can be tested with mocked API responses.
4. **Manual Testing:** Deploy to VM and test in real Telegram chat.

## Deployment Flow

1. Build and push code to GitHub
2. Pull changes on VM: `cd ~/se-toolkit-lab-7 && git pull`
3. Install dependencies: `cd bot && uv sync`
4. Restart bot: `pkill -f "bot.py"; nohup uv run bot.py > bot.log 2>&1 &`
5. Test in Telegram: send `/start` to bot

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM API rate limits | Cache responses, implement retry logic |
| Backend downtime | Graceful error messages, health check before queries |
| Token exposure | Never commit `.env.bot.secret`, use gitignore |
| Network issues in Docker | Use service names, not localhost, in container URLs |
