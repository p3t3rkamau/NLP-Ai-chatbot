"""
model.py - Feed-forward Neural Network for intent classification
"""

import torch
import torch.nn as nn


class NeuralNet(nn.Module):
    """
    3-layer fully-connected network with ReLU activations.
    No softmax at the output — CrossEntropyLoss handles that internally.
    """

    def __init__(self, input_size: int, hidden_size: int, num_classes: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)