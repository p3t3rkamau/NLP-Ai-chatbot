"""
app.py - Main Flask Chatbot Application (Optimized)
"""

import os
import json
import random
import datetime

import torch
import requests
import wikipedia
import psutil
import webbrowser
from io import BytesIO

from flask import (
    Flask, render_template, request, jsonify,
    make_response, redirect, url_for, flash
)
from flask_cors import cross_origin
from flask_login import LoginManager, UserMixin, login_required, login_user
from bs4 import BeautifulSoup
from PIL import Image

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

VALID_API_KEYS = os.environ.get("VALID_API_KEYS", "api_key_1,api_key_2,api_key_3").split(",")
MAX_REQUESTS_PER_KEY = 100

# ─────────────────────────────────────────────
# Login Manager
# ─────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, username: str, password: str):
        self.id = username
        self.password = password


USERS = {
    "user1": User("user1", "password1"),
    "user2": User("user2", "password2"),
}


@login_manager.user_loader
def load_user(user_id: str):
    return USERS.get(user_id)


# ─────────────────────────────────────────────
# ML Model Loading
# ─────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

with open("intents.json", "r") as f:
    INTENTS = json.load(f)

_data = torch.load("data.pth", map_location=device)
_model = NeuralNet(_data["input_size"], _data["hidden_size"], _data["output_size"]).to(device)
_model.load_state_dict(_data["model_state"])
_model.eval()

ALL_WORDS = _data["all_words"]
TAGS = _data["tags"]

# ─────────────────────────────────────────────
# API Key Usage (persisted to JSON)
# ─────────────────────────────────────────────
API_USAGE_FILE = "api_key_usage.json"

def _load_api_usage() -> dict:
    if os.path.isfile(API_USAGE_FILE):
        with open(API_USAGE_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_api_usage(usage: dict) -> None:
    with open(API_USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)

api_key_usage: dict = _load_api_usage()


# ─────────────────────────────────────────────
# Helper Utilities
# ─────────────────────────────────────────────
CHATLOG = "chatlog.txt"
QUERY_FILE = "query.json"
NAMES_FILE = "names.txt"


def log(label: str, text: str) -> None:
    """Append a timestamped line to chatlog.txt."""
    with open(CHATLOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {label}: {text}\n")


def read_last_query() -> str:
    try:
        with open(QUERY_FILE, "r") as f:
            return json.load(f).get("last_query", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def write_last_query(query: str) -> None:
    with open(QUERY_FILE, "w") as f:
        json.dump({"last_query": query}, f)


def _get_conversation_history() -> list:
    raw = request.cookies.get("conversation_history")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    return []


def _set_conversation_cookie(response, history: list):
    response.set_cookie("conversation_history", json.dumps(history))
    return response


# ─────────────────────────────────────────────
# Chatbot Core Logic
# ─────────────────────────────────────────────
def _neural_response(user_message: str) -> str | None:
    """Run the trained neural net and return a response if confidence > 0.75."""
    sentence = tokenize(user_message)
    X = bag_of_words(sentence, ALL_WORDS)
    X = torch.from_numpy(X.reshape(1, -1)).to(device)

    with torch.no_grad():
        output = _model(X)
    _, predicted = torch.max(output, dim=1)
    prob = torch.softmax(output, dim=1)[0][predicted.item()].item()

    if prob > 0.75:
        tag = TAGS[predicted.item()]
        for intent in INTENTS["intents"]:
            if intent["tag"] == tag:
                return random.choice(intent["responses"])
    return None


def _default_response() -> str:
    defaults = [i["responses"] for i in INTENTS["intents"] if i["tag"] == "Default"]
    return random.choice(defaults[0]) if defaults else "I'm sorry, I don't have an answer for that."


def generate_chatbot_response(user_message: str, last_query: str = "") -> str:
    msg_lower = user_message.lower()
    words = msg_lower.split()

    # ── Pattern matching against intents ─────────────────────────────────────
    for intent in INTENTS["intents"]:
        if intent["tag"] == "Default":
            continue
        for pattern in intent["patterns"]:
            if all(w in words for w in pattern.lower().split()):
                return random.choice(intent["responses"])

    # ── Neural network fallback ───────────────────────────────────────────────
    neural = _neural_response(user_message)
    if neural:
        return neural

    # Single-word messages that didn't match
    if " " not in user_message.strip():
        return "I'm sorry, I didn't understand that. Could you give me a bit more detail?"

    # ── Special command handlers ──────────────────────────────────────────────
    if "google" in words:
        query = msg_lower.replace("google", "").strip()
        webbrowser.open(f"https://google.com/search?q={query}")
        return f"Here's what I found for '{query}' on Google."

    if "beast mode" in msg_lower:
        return _beast_mode(msg_lower.split("beast mode", 1)[1].strip())

    if msg_lower.startswith(("update api", "change api")):
        new_key = user_message[10:].strip()
        return _update_api_key(new_key)

    if all(k in words for k in ["get", "website", "content"]):
        return _website_content(user_message)

    if "who is" in msg_lower:
        return _wikipedia_lookup(user_message.lower().replace("who is", "").strip())

    if "battery" in msg_lower:
        return _battery_status()

    if any(p in msg_lower for p in ["remember my name is", "no my name is",
                                     "wrong my name is", "thats not true my name is"]):
        for phrase in ["remember my name is", "no my name is",
                       "wrong my name is", "thats not true my name is"]:
            if phrase in msg_lower:
                name = msg_lower.replace(phrase, "").strip()
                return _remember_name(name)

    if "time" in msg_lower:
        return f"The current time is {datetime.datetime.now().strftime('%H:%M')}. ⌚"

    if any(p in msg_lower for p in ["what is my name", "whats my name"]):
        return _recall_name()

    if any(p in msg_lower for p in ["fuck u", "fuck you"]):
        return "Whoa, easy there! 😂"

    if "what can you do" in msg_lower or "your capabilities" in msg_lower:
        return _capabilities()

    if msg_lower.startswith("code for "):
        return _code_snippet(msg_lower[9:])

    if "show me a picture" in msg_lower:
        return _fetch_unsplash_image(msg_lower.replace("show me a picture of", "").strip())

    if "clear chat" in msg_lower:
        return redirect(url_for("clear"))

    return _default_response()


# ── Sub-handlers ─────────────────────────────────────────────────────────────

def _beast_mode(query: str) -> str:
    try:
        import openai
        key_path = "api_key.txt"
        if os.path.isfile(key_path):
            with open(key_path) as f:
                openai.api_key = f.read().strip()
        response = openai.Completion.create(
            engine="text-davinci-002", prompt=f"User: {query}\nChatbot:", max_tokens=100
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Beast mode unavailable: {e}"


def _update_api_key(new_key: str) -> str:
    with open("api_key.txt", "w") as f:
        f.write(new_key)
    return "API key updated successfully!"


def _website_content(user_message: str) -> str:
    url = user_message.lower().replace("get website content", "").strip()
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        return soup.get_text()[:2000]  # cap output
    except Exception as e:
        return f"Could not fetch content: {e}"


def _wikipedia_lookup(person: str) -> str:
    try:
        return wikipedia.summary(person, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"There are multiple results for '{e.title}'. Could you be more specific?"
    except wikipedia.exceptions.PageError:
        return f"Sorry, I couldn't find anything about '{person}'."


def _battery_status() -> str:
    battery = psutil.sensors_battery()
    if battery:
        return f"Your battery is at {battery.percent:.0f}%."
    return "I couldn't retrieve the battery level on this device."


def _remember_name(name: str) -> str:
    with open(NAMES_FILE, "w") as f:
        f.write(name)
    return f"Got it! I'll remember that your name is {name}. 👍"


def _recall_name() -> str:
    if os.path.isfile(NAMES_FILE):
        with open(NAMES_FILE) as f:
            name = f.read().strip()
        return f"Your name is {name}!" if name else "I don't seem to have your name saved."
    return "I don't have your name saved yet. Tell me with 'remember my name is ...'."


def _capabilities() -> str:
    return (
        "Here's what I can do:\n"
        "• Answer questions using a trained intent model\n"
        "• Search Google for you\n"
        "• Look up people on Wikipedia\n"
        "• Remember and recall your name\n"
        "• Tell you the current time and battery level\n"
        "• Fetch text content from websites\n"
        "• Show pictures from Unsplash\n"
        "• Generate code snippets\n"
        "• Run OpenAI completions in 'beast mode'\n"
        "• Manage conversation history"
    )


def _code_snippet(query: str) -> str:
    snippets = {
        "center": (
            "HTML:\n```html\n<div class='centered'>Content</div>\n```\n"
            "CSS:\n```css\n.centered { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); }\n```"
        ),
        "responsive navbar": (
            "```css\n#navbar { display:flex; flex-wrap:wrap; justify-content:space-between; }\n"
            "#navbar ul { display:flex; flex-direction:column; }\n#navbar li { padding:1rem; }\n```"
        ),
        "slider": (
            "```css\n.slider { max-width:100%; position:relative; }\n"
            ".slider img { width:100%; }\n"
            ".slider .prev,.slider .next { position:absolute; top:50%; transform:translateY(-50%); }\n```"
        ),
    }
    for key, val in snippets.items():
        if key in query:
            return val
    return "No code snippet found for that query. Try 'center', 'responsive navbar', or 'slider'."


def _fetch_unsplash_image(search_term: str) -> str:
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "YOUR_KEY_HERE")
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos/",
            headers={"Authorization": f"Client-ID {access_key}"},
            params={"query": search_term, "per_page": 2},
            timeout=10,
        )
        results = resp.json().get("results", [])
        if not results:
            return "I couldn't find any pictures for that."
        urls = [r["urls"]["regular"] for r in results]
        tags = "".join(f'<img src="{u}" style="max-width:100%;margin:4px 0;" />' for u in urls)
        return f"Here are some pictures of {search_term}: {tags}"
    except Exception as e:
        return f"Image search failed: {e}"


def _store_feedback(user_message: str, chatbot_response: str, feedback_type: str) -> None:
    entry = {
        "timestamp": str(datetime.datetime.now()),
        "user_message": user_message,
        "chatbot_response": chatbot_response,
        "feedback_type": feedback_type,
    }
    with open("feedback.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def main_page():
    return render_template("main_page.html")


@app.route("/index")
def home():
    history = _get_conversation_history()
    return render_template("index.html", conversation_history=history, show_game_input=False)


@app.route("/chat", methods=["POST"])
@cross_origin()
def chat():
    try:
        user_message = request.form["user_message"]
        last_query = read_last_query()
        chatbot_response = generate_chatbot_response(user_message, last_query)
        write_last_query(user_message)

        history = _get_conversation_history()
        history.append({"user": user_message, "chatbot": chatbot_response})

        log("User", user_message)
        log("Chatbot", chatbot_response)

        resp = make_response(
            render_template("index.html", chatbot_response=chatbot_response,
                            conversation_history=history, show_game_input=False)
        )
        return _set_conversation_cookie(resp, history)

    except KeyError:
        return _chat_error("Missing user_message field.")
    except Exception as e:
        return _chat_error(str(e))


def _chat_error(msg: str):
    log("error", msg)
    return render_template("index.html", chatbot_response="", error_message=msg)


# ── Public REST API ───────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
@cross_origin()
def chatbot_api():
    try:
        body = request.get_json(force=True)
        user_message = body["user_message"]
        api_key = body.get("api_key")

        if api_key not in VALID_API_KEYS:
            return jsonify({"error": "Invalid API key"}), 401

        usage = api_key_usage.get(api_key, 0)
        if usage >= MAX_REQUESTS_PER_KEY:
            return jsonify({"error": "Request limit reached. Please upgrade your plan."}), 403

        api_key_usage[api_key] = usage + 1
        _save_api_usage(api_key_usage)

        chatbot_response = generate_chatbot_response(user_message, read_last_query())
        write_last_query(user_message)

        history = _get_conversation_history()
        history.append({"user": user_message, "chatbot": chatbot_response})

        log("User", user_message)
        log("Chatbot", chatbot_response)

        resp = jsonify({"chatbot_response": chatbot_response, "conversation_history": history})
        return _set_conversation_cookie(resp, history)

    except KeyError:
        return jsonify({"error": "Missing user_message"}), 400
    except Exception as e:
        log("error", str(e))
        return jsonify({"error": str(e)}), 500


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = USERS.get(username)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("view_chatlog"))
        return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")


@app.route("/admin/chatlog")
@login_required
def view_chatlog():
    lines = []
    try:
        with open(CHATLOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "User:" in line:
                    lines.append((line, "user"))
                elif "Chatbot:" in line:
                    lines.append((line, "chatbot"))
                elif "error:" in line:
                    lines.append((line, "error"))
                else:
                    lines.append((line, ""))
    except FileNotFoundError:
        pass
    return render_template("chatlog.html", lines=lines)


@app.route("/admin/clear_chatlog", methods=["POST"])
@login_required
def clear_chatlog():
    open(CHATLOG, "w").close()
    flash("Chat log cleared.")
    return redirect(url_for("view_chatlog"))


# ── Misc routes ───────────────────────────────────────────────────────────────

@app.route("/clear")
def clear():
    resp = make_response(render_template("index.html", conversation_history=[]))
    resp.set_cookie("conversation_history", "", expires=0)
    return resp


@app.route("/intents")
def get_intents():
    with open("intents.json") as f:
        return json.load(f)


@app.route("/api_usage")
def get_api_usage():
    return jsonify(api_key_usage)


@app.route("/users-feedback")
def chatbot_ratings():
    with open("feedback.json", encoding="utf-8") as f:
        return f.read()


@app.route("/feedback", methods=["POST"])
@cross_origin()
def feedback():
    try:
        data = request.get_json(force=True)
        _store_feedback(data["userMessage"], data["chatbotResponse"], data["feedbackType"])
        return "", 204
    except (KeyError, TypeError):
        return "", 400
    except Exception as e:
        log("error", str(e))
        return "", 500


@app.route("/game", methods=["GET", "POST"])
def game():
    if request.method == "POST":
        player = request.form["player_choice"]
        choices = ["rock", "paper", "scissors"]
        if player not in choices:
            return render_template("index.html", error_message="Choose rock, paper, or scissors.")
        computer = random.choice(choices)
        wins = {("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")}
        if player == computer:
            result = "It's a draw! 🤝"
        elif (player, computer) in wins:
            result = "You win! 🎉"
        else:
            result = "Computer wins! 🤖"
        return render_template("index.html", result=result, show_game_input=False)
    return render_template("index.html", show_game_input=False)


@app.route("/embedded-code")
def embedded_code():
    return render_template("embedded_code.html")


@app.route("/chatpage")
def chatpage():
    return render_template("chat.html")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)