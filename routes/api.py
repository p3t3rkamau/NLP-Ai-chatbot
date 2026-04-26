"""
routes/api.py - Public REST API routes
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from response_generator import generate_chatbot_response
from conversation import get_conversation_history, set_conversation_cookie, add_to_history
from api_usage import load_api_usage, get_usage_count, increment_usage
from logging_utils import log, read_last_query, write_last_query
from config import VALID_API_KEYS, MAX_REQUESTS_PER_KEY

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Load API usage on startup
api_key_usage = load_api_usage()


@api_bp.route("/chat", methods=["POST"])
@cross_origin()
def chatbot_api():
    """REST API endpoint for chatbot interactions."""
    try:
        body = request.get_json(force=True)
        user_message = body["user_message"]
        api_key = body.get("api_key")

        if api_key not in VALID_API_KEYS:
            return jsonify({"error": "Invalid API key"}), 401

        usage = get_usage_count(api_key, api_key_usage)
        if usage >= MAX_REQUESTS_PER_KEY:
            return jsonify({"error": "Request limit reached. Please upgrade your plan."}), 403

        # Increment usage and generate response
        increment_usage(api_key, api_key_usage)
        chatbot_response = generate_chatbot_response(user_message, read_last_query())
        write_last_query(user_message)

        history = get_conversation_history()
        history = add_to_history(history, user_message, chatbot_response)

        log("User", user_message)
        log("Chatbot", chatbot_response)

        resp = jsonify({"chatbot_response": chatbot_response, "conversation_history": history})
        return set_conversation_cookie(resp, history)

    except KeyError:
        return jsonify({"error": "Missing user_message"}), 400
    except Exception as e:
        log("error", str(e))
        return jsonify({"error": str(e)}), 500
