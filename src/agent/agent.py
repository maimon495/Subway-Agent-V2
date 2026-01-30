"""NYC Subway Agent using LangChain and Groq."""
import os
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from .prompts import SYSTEM_PROMPT
from .tools import ALL_TOOLS

# Conversation history (excluding system message which is added per-request)
_conversation_history: list[BaseMessage] = []

# Agent instance (lazy initialized)
_agent = None


def _get_agent():
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")

        # Initialize Groq with Llama
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            api_key=api_key,
        )

        # Create the agent with tools
        _agent = create_react_agent(llm, ALL_TOOLS)

    return _agent


async def chat(user_message: str) -> str:
    """Send a message to the subway agent and get a response."""
    agent = _get_agent()

    # Add user message to history
    _conversation_history.append(HumanMessage(content=user_message))

    try:
        # Build messages with system prompt first
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + _conversation_history

        # Invoke the agent
        result = await agent.ainvoke({
            "messages": messages,
        })

        # Extract the final response
        messages = result.get("messages", [])
        if messages:
            final_message = messages[-1]
            response_text = final_message.content if hasattr(final_message, "content") else str(final_message)

            # Add assistant response to history
            _conversation_history.append(AIMessage(content=response_text))

            return response_text

        return "I couldn't generate a response. Please try again."

    except Exception as e:
        # Remove the user message on error so it can be retried
        _conversation_history.pop()
        raise e


def chat_sync(user_message: str) -> str:
    """Synchronous version of chat for CLI usage."""
    import asyncio
    return asyncio.run(chat(user_message))


def clear_history() -> None:
    """Clear conversation history."""
    _conversation_history.clear()


def get_history() -> list[BaseMessage]:
    """Get current conversation history."""
    return list(_conversation_history)
