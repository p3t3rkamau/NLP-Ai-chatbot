"""
logging_utils.py - Logging and file management utilities
"""

import os
import json
import datetime
from config import CHATLOG_FILE, QUERY_FILE, NAMES_FILE, FEEDBACK_FILE


def log(label: str, text: str) -> None:
    """Append a timestamped line to the chatlog."""
    with open(CHATLOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {label}: {text}\n")


def read_last_query() -> str:
    """Read the last user query from file."""
    try:
        with open(QUERY_FILE, "r") as f:
            return json.load(f).get("last_query", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def write_last_query(query: str) -> None:
    """Write the last user query to file."""
    with open(QUERY_FILE, "w") as f:
        json.dump({"last_query": query}, f)


def remember_name(name: str) -> None:
    """Store user's name to file."""
    with open(NAMES_FILE, "w") as f:
        f.write(name)


def recall_name() -> str:
    """Retrieve user's stored name."""
    if os.path.isfile(NAMES_FILE):
        with open(NAMES_FILE) as f:
            name = f.read().strip()
        return name if name else ""
    return ""


def store_feedback(user_message: str, chatbot_response: str, feedback_type: str) -> None:
    """Store user feedback to file."""
    entry = {
        "timestamp": str(datetime.datetime.now()),
        "user_message": user_message,
        "chatbot_response": chatbot_response,
        "feedback_type": feedback_type,
    }
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def clear_chatlog() -> None:
    """Clear the chatlog file."""
    open(CHATLOG_FILE, "w").close()


def read_chatlog() -> list:
    """Read all entries from chatlog."""
    lines = []
    try:
        with open(CHATLOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "User:" in line:
                    lines.append((line, "user"))
                elif "Chatbot:" in line:
                    lines.append((line, "chatbot"))
                elif "error:" in line:
                    lines.append((line, "error"))
                else:
                    lines.append((line, ""))
    except FileNotFoundError:
        pass
    return lines
