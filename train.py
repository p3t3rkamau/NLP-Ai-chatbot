"""
train.py - Train the intent classification neural network and save weights.

Usage:
    python train.py

Outputs:
    data.pth  — saved model weights + metadata (loaded by app.py at startup)
"""

import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from nltk_utils import bag_of_words, tokenize, stem
from model import NeuralNet

# ─────────────────────────────────────────────
# Hyper-parameters  (tweak these to improve accuracy)
# ─────────────────────────────────────────────
NUM_EPOCHS   = 1000
BATCH_SIZE   = 8
LEARNING_RATE = 0.001
HIDDEN_SIZE  = 8

# Tips:
#   • Increase NUM_EPOCHS if final loss is still high
#   • Lower LEARNING_RATE if loss oscillates wildly
#   • Increase HIDDEN_SIZE for more complex intent sets
#   • Add Dropout(0.3) between layers to combat overfitting

# ─────────────────────────────────────────────
# Load & pre-process intents
# ─────────────────────────────────────────────
with open("intents.json", "r") as f:
    intents = json.load(f)

IGNORE = {"?", ".", "!"}

all_words: list[str] = []
tags:      list[str] = []
xy:        list[tuple] = []        # (tokenised_pattern, tag)

for intent in intents["intents"]:
    tag = intent["tag"]
    tags.append(tag)
    for pattern in intent["patterns"]:
        tokens = tokenize(pattern)
        all_words.extend(tokens)
        xy.append((tokens, tag))

all_words = sorted(set(stem(w) for w in all_words if w not in IGNORE))
tags      = sorted(set(tags))

print(f"{len(xy)} patterns | {len(tags)} tags | {len(all_words)} unique stemmed words")

# ─────────────────────────────────────────────
# Build training tensors
# ─────────────────────────────────────────────
X_train = np.array([bag_of_words(tokens, all_words) for tokens, _ in xy])
y_train = np.array([tags.index(tag) for _, tag in xy])

INPUT_SIZE  = len(X_train[0])
OUTPUT_SIZE = len(tags)
print(f"Input size: {INPUT_SIZE}  |  Output size: {OUTPUT_SIZE}")


class ChatDataset(Dataset):
    def __init__(self):
        self.x = X_train
        self.y = y_train

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]


loader = DataLoader(
    ChatDataset(),
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
)

# ─────────────────────────────────────────────
# Model, loss, optimiser
# ─────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model  = NeuralNet(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE).to(device)

criterion = nn.CrossEntropyLoss()
optimiser = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

# ─────────────────────────────────────────────
# Training loop
# ─────────────────────────────────────────────
for epoch in range(1, NUM_EPOCHS + 1):
    for words, labels in loader:
        words  = words.to(device)
        labels = labels.to(dtype=torch.long).to(device)

        outputs = model(words)
        loss    = criterion(outputs, labels)

        optimiser.zero_grad()
        loss.backward()
        optimiser.step()

    if epoch % 100 == 0:
        print(f"Epoch [{epoch:4d}/{NUM_EPOCHS}]  Loss: {loss.item():.4f}")

print(f"\nFinal loss: {loss.item():.4f}")

# ─────────────────────────────────────────────
# Save checkpoint
# ─────────────────────────────────────────────
checkpoint = {
    "model_state": model.state_dict(),
    "input_size":  INPUT_SIZE,
    "hidden_size": HIDDEN_SIZE,
    "output_size": OUTPUT_SIZE,
    "all_words":   all_words,
    "tags":        tags,
}

torch.save(checkpoint, "data.pth")
print("Training complete — weights saved to data.pth")