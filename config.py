"""Application configuration."""

import os

# Flask Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
DEBUG = os.environ.get("DEBUG", "False") == "True"
THREADED = True

# Authentication
LOGIN_VIEW = "admin.login"
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-this-password")

# API Configuration
VALID_API_KEYS = [k.strip() for k in os.environ.get("VALID_API_KEYS", "api_key_1,api_key_2,api_key_3").split(",") if k.strip()]
MAX_REQUESTS_PER_KEY = int(os.environ.get("MAX_REQUESTS_PER_KEY", "100"))

# Local rate limit (UI + API fallback)
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "30"))

# File Paths
INTENTS_FILE = "intents.json"
MODEL_FILE = "data.pth"
API_USAGE_FILE = "api_key_usage.json"
CHATLOG_FILE = "chatlog.txt"
QUERY_FILE = "query.json"
NAMES_FILE = "names.txt"
FEEDBACK_FILE = "feedback.json"
API_KEY_FILE = "api_key.txt"

# File size caps (rotate when exceeded)
MAX_CHATLOG_BYTES = int(os.environ.get("MAX_CHATLOG_BYTES", str(2 * 1024 * 1024)))
MAX_FEEDBACK_BYTES = int(os.environ.get("MAX_FEEDBACK_BYTES", str(2 * 1024 * 1024)))
MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "20"))
MAX_MESSAGE_CHARS = int(os.environ.get("MAX_MESSAGE_CHARS", "2000"))

# External APIs
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# Neural Network Thresholds
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.75"))
SEMANTIC_THRESHOLD = float(os.environ.get("SEMANTIC_THRESHOLD", "0.6"))
