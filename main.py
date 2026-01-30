#!/usr/bin/env python3
"""NYC Subway Agent CLI - Real-time train arrivals and route planning."""
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - set DEBUG=1 env var for verbose output
log_level = logging.DEBUG if os.getenv("DEBUG") else logging.WARNING
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

from src.agent import chat, clear_history

WELCOME_MESSAGE = """
NYC Subway Agent v1.0 (Python)
==============================
I can help you with:
- Train arrivals: "When is the next uptown N at Union Square?"
- Route planning: "Best route from South Ferry to Penn Station"

Type 'quit' to exit, 'clear' to reset conversation.
"""


async def main():
    print(WELCOME_MESSAGE)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ("quit", "exit"):
                print("\nGoodbye!")
                break

            if user_input.lower() == "clear":
                clear_history()
                print("\nConversation cleared.")
                continue

            print("\nAgent: Thinking...")

            try:
                response = await chat(user_input)
                print(f"\nAgent: {response}")
            except ValueError as e:
                if "GROQ_API_KEY" in str(e):
                    print("\nError: GROQ_API_KEY environment variable is not set.")
                    print("Please set it with: export GROQ_API_KEY=your_key_here")
                else:
                    print(f"\nError: {e}")
            except Exception as e:
                print(f"\nError: {e}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
