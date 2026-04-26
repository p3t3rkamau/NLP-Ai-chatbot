"""
conversation.py - Conversation history and cookie management
"""

import json
from flask import request


def get_conversation_history() -> list:
    """Retrieve conversation history from cookie."""
    raw = request.cookies.get("conversation_history")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    return []


def set_conversation_cookie(response, history: list):
    """Set conversation history in response cookie."""
    response.set_cookie("conversation_history", json.dumps(history))
    return response


def add_to_history(history: list, user_msg: str, bot_msg: str) -> list:
    """Add a user-bot message pair to conversation history."""
    history.append({"user": user_msg, "chatbot": bot_msg})
    return history
