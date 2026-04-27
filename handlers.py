"""Specialized command handlers."""

import ipaddress
import os
import random
from urllib.parse import urlparse

import requests
import wikipedia
import psutil
from bs4 import BeautifulSoup
from flask_login import current_user

from config import UNSPLASH_ACCESS_KEY, API_KEY_FILE
from logging_utils import remember_name, recall_name


def beast_mode(query: str) -> str:
    """Run OpenAI chat completion for beast mode queries."""
    try:
        import openai
        api_key = None
        if os.path.isfile(API_KEY_FILE):
            with open(API_KEY_FILE, encoding="utf-8") as f:
                api_key = f.read().strip() or None
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query}],
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Beast mode is currently unavailable."


def update_api_key(new_key: str) -> str:
    """Update the OpenAI API key (admin only)."""
    if not current_user.is_authenticated:
        return "Only authenticated admins can update API keys."
    with open(API_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(new_key)
    return "API key updated successfully."


def _is_private_host(hostname: str) -> bool:
    if not hostname:
        return True
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return False


def get_website_content(user_message: str) -> str:
    """Fetch and return website content with SSRF protection."""
    url = user_message.lower().replace("get website content", "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return "Only http/https URLs are allowed."
    if _is_private_host(parsed.hostname or ""):
        return "That URL is not allowed."

    try:
        resp = requests.get(url, timeout=10, allow_redirects=False)
        soup = BeautifulSoup(resp.content, "html.parser")
        return soup.get_text()[:2000]
    except Exception:
        return "Could not fetch website content."


def wikipedia_lookup(person: str) -> str:
    try:
        return wikipedia.summary(person, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"There are multiple results for '{e.title}'. Could you be more specific?"
    except wikipedia.exceptions.PageError:
        return f"Sorry, I couldn't find anything about '{person}'."


def get_battery_status() -> str:
    battery = psutil.sensors_battery()
    if battery:
        return f"Your battery is at {battery.percent:.0f}%."
    return "I couldn't retrieve the battery level on this device."


def get_name_response(name: str) -> str:
    safe_name = name.strip()[:100]
    remember_name(safe_name)
    return f"Got it! I'll remember that your name is {safe_name}. 👍"


def recall_user_name() -> str:
    name = recall_name()
    if name:
        return f"Your name is {name}!"
    return "I don't have your name saved yet. Tell me with 'remember my name is ...'."


def get_capabilities() -> str:
    return (
        "Here's what I can do:\n"
        "• Answer questions with intents + semantic matching\n"
        "• Use an LLM fallback for open-ended chats\n"
        "• Search Google, Wikipedia, and images\n"
        "• Remember your name and show battery/time"
    )


def get_code_snippet(query: str) -> str:
    snippets = {
        "center": "Use flexbox: .container{display:flex;justify-content:center;align-items:center;}",
        "responsive navbar": "Use media queries + flex-wrap for nav items.",
        "slider": "Use overflow hidden and transform translateX for slides.",
    }
    for key, val in snippets.items():
        if key in query:
            return val
    return "No code snippet found for that query."


def fetch_unsplash_image(search_term: str) -> str:
    """Return image results as [img]URL[/img] markers (rendered by client JS)."""
    if not UNSPLASH_ACCESS_KEY:
        return "Image search is not configured."
    safe_term = search_term.strip()[:100]
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos/",
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            params={"query": safe_term, "per_page": 2},
            timeout=10,
        )
        results = resp.json().get("results", [])
        if not results:
            return "I couldn't find any pictures for that."
        img_markers = " ".join(
            f"[img]{r['urls']['regular']}[/img]"
            for r in results
            if r.get("urls", {}).get("regular", "").startswith("https://")
        )
        return f"Here are some pictures of {safe_term}: {img_markers}"
    except Exception:
        return "Image search failed."


def play_rock_paper_scissors(player_choice: str) -> str:
    choices = ["rock", "paper", "scissors"]
    if player_choice not in choices:
        return "Choose rock, paper, or scissors."
    computer = random.choice(choices)
    wins = {("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")}
    if player_choice == computer:
        return "It's a draw! 🤝"
    return "You win! 🎉" if (player_choice, computer) in wins else "Computer wins! 🤖"
