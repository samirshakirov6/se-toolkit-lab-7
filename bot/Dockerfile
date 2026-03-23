# Bot Dockerfile
# Uses uv and pyproject.toml exclusively - no requirements.txt

FROM python:3.14-slim

WORKDIR /app/bot

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy bot project files
COPY bot/pyproject.toml bot/uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy bot source code
COPY bot/ ./

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["uv", "run", "python", "bot.py"]
