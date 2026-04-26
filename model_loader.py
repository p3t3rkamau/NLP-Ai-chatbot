"""
model_loader.py - ML model loading and initialization
"""

import json
import torch
from model import NeuralNet
from config import MODEL_FILE, INTENTS_FILE

# Initialize device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load intents
with open(INTENTS_FILE, "r") as f:
    INTENTS = json.load(f)

# Load model checkpoint
_data = torch.load(MODEL_FILE, map_location=device)
_model = NeuralNet(_data["input_size"], _data["hidden_size"], _data["output_size"]).to(device)
state = _data["model_state"]
if "l1.weight" in state:
    state = {
        "network.0.weight": state["l1.weight"],
        "network.0.bias": state["l1.bias"],
        "network.2.weight": state["l2.weight"],
        "network.2.bias": state["l2.bias"],
        "network.4.weight": state["l3.weight"],
        "network.4.bias": state["l3.bias"],
    }
_model.load_state_dict(state, strict=False)
_model.eval()

# Extract model metadata
ALL_WORDS = _data["all_words"]
TAGS = _data["tags"]


def get_model() -> NeuralNet:
    """Get the loaded neural network model."""
    return _model


def get_device() -> torch.device:
    """Get the torch device (CPU or CUDA)."""
    return device


def get_intents() -> dict:
    """Get the intents dictionary."""
    return INTENTS


def get_all_words() -> list[str]:
    """Get the complete vocabulary."""
    return ALL_WORDS


def get_tags() -> list[str]:
    """Get all intent tags."""
    return TAGS
