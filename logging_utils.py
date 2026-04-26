"""Logging and file management utilities."""

import os
import json
import datetime
from config import CHATLOG_FILE, QUERY_FILE, NAMES_FILE, FEEDBACK_FILE, MAX_CHATLOG_BYTES, MAX_FEEDBACK_BYTES


def _rotate_if_needed(file_path: str, max_bytes: int) -> None:
    if os.path.isfile(file_path) and os.path.getsize(file_path) >= max_bytes:
        backup = f"{file_path}.1"
        if os.path.isfile(backup):
            os.remove(backup)
        os.rename(file_path, backup)


def log(label: str, text: str) -> None:
    _rotate_if_needed(CHATLOG_FILE, MAX_CHATLOG_BYTES)
    with open(CHATLOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {label}: {text}\n")


def read_last_query() -> str:
    try:
        with open(QUERY_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last_query", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def write_last_query(query: str) -> None:
    with open(QUERY_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_query": query}, f)


def remember_name(name: str) -> None:
    with open(NAMES_FILE, "w", encoding="utf-8") as f:
        f.write(name)


def recall_name() -> str:
    if os.path.isfile(NAMES_FILE):
        with open(NAMES_FILE, encoding="utf-8") as f:
            name = f.read().strip()
        return name if name else ""
    return ""


def store_feedback(user_message: str, chatbot_response: str, feedback_type: str) -> None:
    _rotate_if_needed(FEEDBACK_FILE, MAX_FEEDBACK_BYTES)
    entry = {
        "timestamp": str(datetime.datetime.now()),
        "user_message": user_message,
        "chatbot_response": chatbot_response,
        "feedback_type": feedback_type,
    }
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_feedback() -> list[str]:
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def clear_chatlog() -> None:
    open(CHATLOG_FILE, "w", encoding="utf-8").close()


def read_chatlog() -> list:
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
