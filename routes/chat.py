"""Main chat routes."""

from flask import Blueprint, render_template, request, make_response, jsonify
from flask_cors import cross_origin
from markupsafe import escape
from response_generator import generate_chatbot_response
from conversation import get_conversation_history, set_conversation_cookie, add_to_history
from logging_utils import log
from rate_limit import is_limited
from config import MAX_MESSAGE_CHARS

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
def main_page():
    return render_template("main_page.html")


@chat_bp.route("/index")
def home():
    history = get_conversation_history()
    return render_template("index.html", conversation_history=history, show_game_input=False)


@chat_bp.route("/chat", methods=["POST"])
@cross_origin()
def chat():
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        if is_limited(f"chat:{ip}"):
            return _chat_error("Rate limit exceeded. Please wait a minute.", status=429)

        user_message = request.form["user_message"][:MAX_MESSAGE_CHARS]
        history = get_conversation_history()
        chatbot_response = generate_chatbot_response(user_message, history)
        chatbot_response = str(escape(chatbot_response))

        history = add_to_history(history, user_message, chatbot_response)

        log("User", user_message)
        log("Chatbot", chatbot_response)

        resp = make_response(
            render_template(
                "index.html",
                chatbot_response=chatbot_response,
                conversation_history=history,
                show_game_input=False,
            )
        )
        return set_conversation_cookie(resp, history)

    except KeyError:
        return _chat_error("Missing user_message field.", status=400)
    except Exception as e:
        return _chat_error(str(e), status=500)


def _chat_error(msg: str, status: int = 200):
    log("error", msg)
    if request.path.startswith("/api/"):
        return jsonify({"error": msg}), status
    return render_template("index.html", chatbot_response="", error_message=msg), status
