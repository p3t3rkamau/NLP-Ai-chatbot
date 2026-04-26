"""Public REST API routes."""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from response_generator import generate_chatbot_response
from conversation import get_conversation_history, set_conversation_cookie, add_to_history
from api_usage import load_api_usage, get_usage_count, increment_usage
from logging_utils import log
from config import VALID_API_KEYS, MAX_REQUESTS_PER_KEY, MAX_MESSAGE_CHARS
from rate_limit import is_limited

api_bp = Blueprint("api", __name__, url_prefix="/api")
api_key_usage = load_api_usage()


@api_bp.route("/chat", methods=["POST"])
@cross_origin()
def chatbot_api():
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        if is_limited(f"api:{ip}"):
            return jsonify({"error": "Rate limit exceeded"}), 429

        body = request.get_json(force=True)
        user_message = body["user_message"][:MAX_MESSAGE_CHARS]
        api_key = body.get("api_key")

        if api_key not in VALID_API_KEYS:
            return jsonify({"error": "Invalid API key"}), 401

        usage = get_usage_count(api_key, api_key_usage)
        if usage >= MAX_REQUESTS_PER_KEY:
            return jsonify({"error": "Request limit reached. Please upgrade your plan."}), 403

        increment_usage(api_key, api_key_usage)
        history = get_conversation_history()
        chatbot_response = generate_chatbot_response(user_message, history)
        history = add_to_history(history, user_message, chatbot_response)

        log("User", user_message)
        log("Chatbot", chatbot_response)

        resp = jsonify({"chatbot_response": chatbot_response, "conversation_history": history})
        return set_conversation_cookie(resp, history)

    except KeyError:
        return jsonify({"error": "Missing user_message"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500
