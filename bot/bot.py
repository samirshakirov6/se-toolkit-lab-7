"""Telegram bot entry point with --test mode."""

import argparse
import sys

from config import settings
from handlers import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_unknown,
)
from handlers.intent_router import process_natural_language


def process_command(command: str) -> str:
    """Process a command string and return the response.
    
    Args:
        command: The command string (e.g., "/start", "/scores lab-01").
        
    Returns:
        Response text to send to the user.
    """
    if not command.startswith("/"):
        # Natural language query - use LLM intent router
        return process_natural_language(command)

    # Parse command and arguments
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "/start":
        return handle_start()
    elif cmd == "/help":
        return handle_help()
    elif cmd == "/health":
        return handle_health()
    elif cmd == "/labs":
        return handle_labs()
    elif cmd == "/scores":
        return handle_scores(args if args else None)
    else:
        return handle_unknown(cmd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Test mode: run a command and print the response"
    )
    args = parser.parse_args()

    if args.test:
        # Test mode: process command and print to stdout
        response = process_command(args.test)
        print(response)
        sys.exit(0)

    # Normal mode: start Telegram bot (to be implemented in Task 4)
    print("Starting Telegram bot...")
    print("Use --test mode to test commands locally")
    sys.exit(0)


if __name__ == "__main__":
    main()
