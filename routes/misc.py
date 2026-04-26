"""Miscellaneous routes."""

import json
from flask import Blueprint, render_template, request, make_response, jsonify
from flask_cors import cross_origin
from flask_login import login_required
from conversation import clear_history
from logging_utils import store_feedback, log, read_feedback
from api_usage import load_api_usage
from model_loader import get_intents
from handlers import play_rock_paper_scissors

misc_bp = Blueprint("misc", __name__)


@misc_bp.route("/clear")
def clear():
    clear_history()
    resp = make_response(render_template("index.html", conversation_history=[]))
    return resp


@misc_bp.route("/intents")
@login_required
def get_intents_route():
    intents = get_intents()
    return json.dumps(intents)


@misc_bp.route("/api_usage")
@login_required
def get_api_usage():
    usage = load_api_usage()
    return jsonify(usage)


@misc_bp.route("/users-feedback")
@login_required
def chatbot_ratings():
    return "\n".join(read_feedback())


@misc_bp.route("/feedback", methods=["POST"])
@cross_origin()
def feedback():
    try:
        data = request.get_json(force=True)
        store_feedback(data["userMessage"][:2000], data["chatbotResponse"][:2000], data["feedbackType"][:64])
        return "", 204
    except (KeyError, TypeError):
        return jsonify({"error": "Invalid feedback payload"}), 400
    except Exception as e:
        log("error", str(e))
        return jsonify({"error": "Failed to save feedback"}), 500


@misc_bp.route("/game", methods=["GET", "POST"])
def game():
    if request.method == "POST":
        player = request.form["player_choice"]
        result = play_rock_paper_scissors(player)
        return render_template("index.html", result=result, show_game_input=False)
    return render_template("index.html", show_game_input=False)


@misc_bp.route("/embedded-code")
def embedded_code():
    return render_template("embedded_code.html")


@misc_bp.route("/chatpage")
def chatpage():
    return render_template("chat.html")
