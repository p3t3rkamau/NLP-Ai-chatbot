"""
flaskapirequest.py - Lightweight client app that proxies requests to the main chatbot API.

Run AFTER app.py is already running on port 5000:
    python flaskapirequest.py   →  http://localhost:5001
"""

from flask import Flask, render_template, request
import os
import requests

app = Flask(__name__)

API_URL    = "http://localhost:5000/api/chat"
API_KEY    = os.environ.get("CHATBOT_API_KEY", "")
TIMEOUT    = 10                   # seconds


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_message = request.form.get("user_message", "").strip()
    if not user_message:
        return render_template("index.html", error_message="Please enter a message.")

    try:
        resp = requests.post(
            API_URL,
            json={"user_message": user_message, "api_key": API_KEY},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return render_template(
            "index.html",
            chatbot_response=data.get("chatbot_response", ""),
            conversation_history=data.get("conversation_history", []),
        )

    except requests.exceptions.ConnectionError:
        return render_template("index.html", error_message="Cannot reach the chatbot server. Is app.py running?")
    except requests.exceptions.Timeout:
        return render_template("index.html", error_message="The chatbot server timed out. Try again.")
    except Exception as e:
        return render_template("index.html", error_message=str(e))


if __name__ == "__main__":
    app.run(debug=True, port=5001)