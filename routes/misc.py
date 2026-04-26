"""
routes/misc.py - Miscellaneous routes
"""

import json
import random
from flask import Blueprint, render_template, request, make_response, jsonify
from flask_cors import cross_origin
from conversation import get_conversation_history, set_conversation_cookie
from logging_utils import store_feedback, log
from api_usage import load_api_usage
from model_loader import get_intents
from handlers import play_rock_paper_scissors

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/clear")
def clear():
    """Clear conversation history."""
    resp = make_response(render_template("index.html", conversation_history=[]))
    resp.set_cookie("conversation_history", "", expires=0)
    return resp


@misc_bp.route("/intents")
def get_intents_route():
    """Get intents data."""
    intents = get_intents()
    return json.dumps(intents)


@misc_bp.route("/api_usage")
def get_api_usage():
    """Get API usage statistics."""
    usage = load_api_usage()
    return jsonify(usage)


@misc_bp.route("/users-feedback")
def chatbot_ratings():
    """Get user feedback."""
    try:
        with open("feedback.json", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


@misc_bp.route("/feedback", methods=["POST"])
@cross_origin()
def feedback():
    """Store user feedback."""
    try:
        data = request.get_json(force=True)
        store_feedback(data["userMessage"], data["chatbotResponse"], data["feedbackType"])
        return "", 204
    except (KeyError, TypeError):
        return "", 400
    except Exception as e:
        log("error", str(e))
        return "", 500


@misc_bp.route("/game", methods=["GET", "POST"])
def game():
    """Rock-paper-scissors game."""
    if request.method == "POST":
        player = request.form["player_choice"]
        result = play_rock_paper_scissors(player)
        return render_template("index.html", result=result, show_game_input=False)
    return render_template("index.html", show_game_input=False)


@misc_bp.route("/embedded-code")
def embedded_code():
    """Embedded chatbot code page."""
    return render_template("embedded_code.html")


@misc_bp.route("/chatpage")
def chatpage():
    """Chat page."""
    return render_template("chat.html")
