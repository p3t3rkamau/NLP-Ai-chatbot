"""Conversation history management (server-side by session id)."""

import uuid
from flask import session
from config import MAX_HISTORY_MESSAGES

_SESSION_HISTORY: dict[str, list[dict[str, str]]] = {}


def _ensure_session_id() -> str:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


def get_conversation_history() -> list:
    """Retrieve conversation history from in-memory server storage."""
    sid = _ensure_session_id()
    return list(_SESSION_HISTORY.get(sid, []))


def set_conversation_cookie(response, history: list):
    """Compatibility helper; conversation is now stored server-side."""
    sid = _ensure_session_id()
    _SESSION_HISTORY[sid] = history[-MAX_HISTORY_MESSAGES:]
    return response


def add_to_history(history: list, user_msg: str, bot_msg: str) -> list:
    """Add a user-bot message pair and enforce max history length."""
    history.append({"user": user_msg, "chatbot": bot_msg})
    return history[-MAX_HISTORY_MESSAGES:]


def clear_history() -> None:
    sid = _ensure_session_id()
    _SESSION_HISTORY.pop(sid, None)
