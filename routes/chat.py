"""
routes/chat.py - Main chat routes
"""

from flask import Blueprint, render_template, request, make_response
from flask_cors import cross_origin
from response_generator import generate_chatbot_response
from conversation import get_conversation_history, set_conversation_cookie, add_to_history
from logging_utils import log, read_last_query, write_last_query

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
def main_page():
    """Render the main landing page."""
    return render_template("main_page.html")


@chat_bp.route("/index")
def home():
    """Render the chat interface."""
    history = get_conversation_history()
    return render_template("index.html", conversation_history=history, show_game_input=False)


@chat_bp.route("/chat", methods=["POST"])
@cross_origin()
def chat():
    """Handle chat messages from the web interface."""
    try:
        user_message = request.form["user_message"]
        last_query = read_last_query()
        chatbot_response = generate_chatbot_response(user_message, last_query)
        write_last_query(user_message)

        history = get_conversation_history()
        history = add_to_history(history, user_message, chatbot_response)

        log("User", user_message)
        log("Chatbot", chatbot_response)

        resp = make_response(
            render_template("index.html", chatbot_response=chatbot_response,
                            conversation_history=history, show_game_input=False)
        )
        return set_conversation_cookie(resp, history)

    except KeyError:
        return _chat_error("Missing user_message field.")
    except Exception as e:
        return _chat_error(str(e))


def _chat_error(msg: str):
    """Render chat page with error message."""
    log("error", msg)
    return render_template("index.html", chatbot_response="", error_message=msg)
