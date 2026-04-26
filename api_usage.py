"""
api_usage.py - API key usage tracking and persistence
"""

import os
import json
from config import API_USAGE_FILE


def load_api_usage() -> dict:
    """Load API usage data from file."""
    if os.path.isfile(API_USAGE_FILE):
        with open(API_USAGE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_api_usage(usage: dict) -> None:
    """Save API usage data to file."""
    with open(API_USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)


def increment_usage(api_key: str, usage_dict: dict) -> dict:
    """Increment the request count for an API key."""
    usage_dict[api_key] = usage_dict.get(api_key, 0) + 1
    save_api_usage(usage_dict)
    return usage_dict


def get_usage_count(api_key: str, usage_dict: dict) -> int:
    """Get the current usage count for an API key."""
    return usage_dict.get(api_key, 0)
