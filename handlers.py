"""
handlers.py - Specialized command handlers
"""

import os
import random
import requests
import wikipedia
import psutil
import webbrowser
from bs4 import BeautifulSoup
from config import UNSPLASH_ACCESS_KEY, API_KEY_FILE
from logging_utils import remember_name, recall_name


def beast_mode(query: str) -> str:
    """Run OpenAI completion for beast mode queries."""
    try:
        import openai
        if os.path.isfile(API_KEY_FILE):
            with open(API_KEY_FILE) as f:
                openai.api_key = f.read().strip()
        response = openai.Completion.create(
            engine="text-davinci-002", prompt=f"User: {query}\nChatbot:", max_tokens=100
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Beast mode unavailable: {e}"


def update_api_key(new_key: str) -> str:
    """Update the OpenAI API key."""
    with open(API_KEY_FILE, "w") as f:
        f.write(new_key)
    return "API key updated successfully!"


def get_website_content(user_message: str) -> str:
    """Fetch and return website content."""
    url = user_message.lower().replace("get website content", "").strip()
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        return soup.get_text()[:2000]  # cap output
    except Exception as e:
        return f"Could not fetch content: {e}"


def wikipedia_lookup(person: str) -> str:
    """Look up a person on Wikipedia."""
    try:
        return wikipedia.summary(person, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"There are multiple results for '{e.title}'. Could you be more specific?"
    except wikipedia.exceptions.PageError:
        return f"Sorry, I couldn't find anything about '{person}'."


def get_battery_status() -> str:
    """Get the device battery status."""
    battery = psutil.sensors_battery()
    if battery:
        return f"Your battery is at {battery.percent:.0f}%."
    return "I couldn't retrieve the battery level on this device."


def get_name_response(name: str) -> str:
    """Remember and confirm user's name."""
    remember_name(name)
    return f"Got it! I'll remember that your name is {name}. 👍"


def recall_user_name() -> str:
    """Recall the user's stored name."""
    name = recall_name()
    if name:
        return f"Your name is {name}!"
    return "I don't have your name saved yet. Tell me with 'remember my name is ...'."


def get_capabilities() -> str:
    """Return list of chatbot capabilities."""
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


def get_code_snippet(query: str) -> str:
    """Return code snippets for common patterns."""
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


def fetch_unsplash_image(search_term: str) -> str:
    """Fetch images from Unsplash API."""
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos/",
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
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


def play_rock_paper_scissors(player_choice: str) -> str:
    """Play a round of rock-paper-scissors."""
    choices = ["rock", "paper", "scissors"]
    if player_choice not in choices:
        return "Choose rock, paper, or scissors."
    computer = random.choice(choices)
    wins = {("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")}
    if player_choice == computer:
        return "It's a draw! 🤝"
    elif (player_choice, computer) in wins:
        return "You win! 🎉"
    else:
        return "Computer wins! 🤖"
