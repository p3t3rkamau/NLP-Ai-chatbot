"""
response_generator.py - Core chatbot response generation logic
"""

import random
import datetime
import torch
from nltk_utils import bag_of_words, tokenize
from model_loader import get_model, get_device, get_intents, get_all_words, get_tags
from config import CONFIDENCE_THRESHOLD
from handlers import (
    beast_mode, get_website_content, wikipedia_lookup, get_battery_status,
    get_name_response, recall_user_name, get_capabilities, get_code_snippet,
    fetch_unsplash_image
)
from logging_utils import write_last_query


def get_neural_response(user_message: str) -> str | None:
    """
    Run the trained neural network and return a response if confidence exceeds threshold.
    """
    model = get_model()
    device = get_device()
    all_words = get_all_words()
    tags = get_tags()
    intents = get_intents()

    sentence = tokenize(user_message)
    X = bag_of_words(sentence, all_words)
    X = torch.from_numpy(X.reshape(1, -1)).to(device)

    with torch.no_grad():
        output = model(X)
    _, predicted = torch.max(output, dim=1)
    prob = torch.softmax(output, dim=1)[0][predicted.item()].item()

    if prob > CONFIDENCE_THRESHOLD:
        tag = tags[predicted.item()]
        for intent in intents["intents"]:
            if intent["tag"] == tag:
                return random.choice(intent["responses"])
    return None


def get_default_response() -> str:
    """Return a default response when no pattern matches."""
    intents = get_intents()
    defaults = [i["responses"] for i in intents["intents"] if i["tag"] == "Default"]
    return random.choice(defaults[0]) if defaults else "I'm sorry, I don't have an answer for that."


def generate_chatbot_response(user_message: str, last_query: str = "") -> str:
    """
    Main response generation function that handles pattern matching,
    special commands, and neural network fallback.
    """
    intents = get_intents()
    msg_lower = user_message.lower()
    words = msg_lower.split()

    # ─── Pattern matching against intents ───────────────────────────────────
    for intent in intents["intents"]:
        if intent["tag"] == "Default":
            continue
        for pattern in intent["patterns"]:
            if all(w in words for w in pattern.lower().split()):
                return random.choice(intent["responses"])

    # ─── Neural network fallback ────────────────────────────────────────────
    neural = get_neural_response(user_message)
    if neural:
        return neural

    # Single-word messages that didn't match
    if " " not in user_message.strip():
        return "I'm sorry, I didn't understand that. Could you give me a bit more detail?"

    # ─── Special command handlers ────────────────────────────────────────────
    if "google" in words:
        query = msg_lower.replace("google", "").strip()
        import webbrowser
        webbrowser.open(f"https://google.com/search?q={query}")
        return f"Here's what I found for '{query}' on Google."

    if "beast mode" in msg_lower:
        return beast_mode(msg_lower.split("beast mode", 1)[1].strip())

    if msg_lower.startswith(("update api", "change api")):
        new_key = user_message[10:].strip()
        from handlers import update_api_key
        return update_api_key(new_key)

    if all(k in words for k in ["get", "website", "content"]):
        return get_website_content(user_message)

    if "who is" in msg_lower:
        return wikipedia_lookup(user_message.lower().replace("who is", "").strip())

    if "battery" in msg_lower:
        return get_battery_status()

    if any(p in msg_lower for p in ["remember my name is", "no my name is",
                                     "wrong my name is", "thats not true my name is"]):
        for phrase in ["remember my name is", "no my name is",
                       "wrong my name is", "thats not true my name is"]:
            if phrase in msg_lower:
                name = msg_lower.replace(phrase, "").strip()
                return get_name_response(name)

    if "time" in msg_lower:
        return f"The current time is {datetime.datetime.now().strftime('%H:%M')}. ⌚"

    if any(p in msg_lower for p in ["what is my name", "whats my name"]):
        return recall_user_name()

    if any(p in msg_lower for p in ["fuck u", "fuck you"]):
        return "Whoa, easy there! 😂"

    if "what can you do" in msg_lower or "your capabilities" in msg_lower:
        return get_capabilities()

    if msg_lower.startswith("code for "):
        return get_code_snippet(msg_lower[9:])

    if "show me a picture" in msg_lower:
        return fetch_unsplash_image(msg_lower.replace("show me a picture of", "").strip())

    if "clear chat" in msg_lower:
        from flask import redirect, url_for
        return redirect(url_for("clear"))

    return get_default_response()
