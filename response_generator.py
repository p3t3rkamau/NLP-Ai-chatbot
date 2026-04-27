"""Core chatbot response generation logic."""

import datetime
import random
from typing import Iterator

import numpy as np
import torch

from nltk_utils import bag_of_words, tokenize
from model_loader import get_model, get_device, get_intents, get_all_words, get_tags
from config import CONFIDENCE_THRESHOLD, SEMANTIC_THRESHOLD, ANTHROPIC_MODEL
from handlers import (
    beast_mode,
    get_website_content,
    wikipedia_lookup,
    get_battery_status,
    get_name_response,
    recall_user_name,
    get_capabilities,
    get_code_snippet,
    fetch_unsplash_image,
)

try:
    from sentence_transformers import SentenceTransformer
    _encoder = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _encoder = None

try:
    import anthropic
    _anthropic_client = anthropic.Anthropic()
except Exception:
    _anthropic_client = None


def _intent_response_by_tag(tag: str) -> str | None:
    intents = get_intents()
    for intent in intents["intents"]:
        if intent["tag"] == tag:
            return random.choice(intent["responses"])
    return None


def get_neural_intent(user_message: str) -> tuple[str | None, float]:
    model = get_model()
    device = get_device()
    all_words = get_all_words()
    tags = get_tags()

    sentence = tokenize(user_message)
    X = bag_of_words(sentence, all_words)
    X = torch.from_numpy(X.reshape(1, -1)).to(device)

    with torch.no_grad():
        output = model(X)
    _, predicted = torch.max(output, dim=1)
    prob = torch.softmax(output, dim=1)[0][predicted.item()].item()
    return (tags[predicted.item()], prob)


def _semantic_match(user_message: str) -> tuple[str | None, float]:
    if _encoder is None:
        return None, 0.0

    intents = get_intents()
    query_vec = _encoder.encode([user_message])[0]
    best_tag, best_score = None, 0.0

    for intent in intents["intents"]:
        tag = intent["tag"]
        if tag == "Default":
            continue
        vecs = _encoder.encode(intent["patterns"])
        scores = np.dot(vecs, query_vec) / (
            np.linalg.norm(vecs, axis=1) * np.linalg.norm(query_vec) + 1e-12
        )
        score = float(np.max(scores))
        if score > best_score:
            best_score = score
            best_tag = tag

    if best_score >= SEMANTIC_THRESHOLD:
        return best_tag, best_score
    return None, best_score


def _build_llm_messages(user_message: str, history: list[dict]) -> list[dict]:
    messages = []
    for turn in history[-10:]:
        if turn.get("user"):
            messages.append({"role": "user", "content": turn["user"]})
        if turn.get("chatbot"):
            messages.append({"role": "assistant", "content": turn["chatbot"]})
    messages.append({"role": "user", "content": user_message})
    return messages


def _llm_fallback(user_message: str, history: list[dict]) -> str | None:
    if _anthropic_client is None:
        return None
    try:
        resp = _anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=512,
            system="You are a helpful assistant.",
            messages=_build_llm_messages(user_message, history),
        )
        return resp.content[0].text
    except Exception:
        return None


def _llm_fallback_streaming(user_message: str, history: list[dict]) -> Iterator[str]:
    try:
        with _anthropic_client.messages.stream(
            model=ANTHROPIC_MODEL,
            max_tokens=512,
            system="You are a helpful assistant.",
            messages=_build_llm_messages(user_message, history),
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception:
        yield get_default_response()


def get_default_response() -> str:
    intents = get_intents()
    defaults = [i["responses"] for i in intents["intents"] if i["tag"] == "Default"]
    return random.choice(defaults[0]) if defaults else "I'm sorry, I don't have an answer for that."


def _try_fast_commands(user_message: str) -> str | None:
    """Return a response string if a fast command matches, otherwise None."""
    msg_lower = user_message.lower().strip()
    words = msg_lower.split()

    if "beast mode" in msg_lower:
        return beast_mode(msg_lower.split("beast mode", 1)[1].strip())
    if all(k in words for k in ["get", "website", "content"]):
        return get_website_content(user_message)
    if "who is" in msg_lower:
        return wikipedia_lookup(msg_lower.replace("who is", "").strip())
    if "battery" in msg_lower:
        return get_battery_status()
    for phrase in [
        "remember my name is",
        "no my name is",
        "wrong my name is",
        "thats not true my name is",
    ]:
        if phrase in msg_lower:
            return get_name_response(msg_lower.replace(phrase, "").strip())
    if any(p in msg_lower for p in ["what is my name", "whats my name"]):
        return recall_user_name()
    if "time" in msg_lower:
        return f"The current time is {datetime.datetime.now().strftime('%H:%M')}. ⌚"
    if "what can you do" in msg_lower or "your capabilities" in msg_lower:
        return get_capabilities()
    if msg_lower.startswith("code for "):
        return get_code_snippet(msg_lower[9:])
    if "show me a picture" in msg_lower:
        return fetch_unsplash_image(msg_lower.replace("show me a picture of", "").strip())
    return None


def generate_chatbot_response(user_message: str, history: list | None = None) -> str:
    history = history or []

    fast = _try_fast_commands(user_message)
    if fast is not None:
        return fast

    tag, prob = get_neural_intent(user_message)
    if tag and prob >= CONFIDENCE_THRESHOLD:
        response = _intent_response_by_tag(tag)
        if response:
            return response

    sem_tag, _ = _semantic_match(user_message)
    if sem_tag:
        response = _intent_response_by_tag(sem_tag)
        if response:
            return response

    llm_response = _llm_fallback(user_message, history)
    if llm_response:
        return llm_response

    return get_default_response()


def generate_chatbot_response_streaming(
    user_message: str, history: list | None = None
) -> Iterator[str]:
    """Yield response tokens; fast commands and intents yield once, LLM streams token-by-token."""
    history = history or []

    fast = _try_fast_commands(user_message)
    if fast is not None:
        yield fast
        return

    tag, prob = get_neural_intent(user_message)
    if tag and prob >= CONFIDENCE_THRESHOLD:
        response = _intent_response_by_tag(tag)
        if response:
            yield response
            return

    sem_tag, _ = _semantic_match(user_message)
    if sem_tag:
        response = _intent_response_by_tag(sem_tag)
        if response:
            yield response
            return

    if _anthropic_client:
        yield from _llm_fallback_streaming(user_message, history)
        return

    yield get_default_response()
