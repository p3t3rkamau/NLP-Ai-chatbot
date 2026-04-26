"""
config.py - Configuration and environment settings
"""

import os

# Flask Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
DEBUG = os.environ.get("DEBUG", "True") == "True"
THREADED = True

# API Configuration
VALID_API_KEYS = os.environ.get("VALID_API_KEYS", "api_key_1,api_key_2,api_key_3").split(",")
MAX_REQUESTS_PER_KEY = 100

# File Paths
INTENTS_FILE = "intents.json"
MODEL_FILE = "data.pth"
API_USAGE_FILE = "api_key_usage.json"
CHATLOG_FILE = "chatlog.txt"
QUERY_FILE = "query.json"
NAMES_FILE = "names.txt"
FEEDBACK_FILE = "feedback.json"
API_KEY_FILE = "api_key.txt"

# External APIs
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "YOUR_KEY_HERE")

# Neural Network Thresholds
CONFIDENCE_THRESHOLD = 0.75
