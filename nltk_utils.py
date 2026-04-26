"""
nltk_utils.py - NLP preprocessing utilities
"""

import numpy as np
import nltk
from nltk.stem.porter import PorterStemmer

# Uncomment once to download the tokenizer data:
# nltk.download('punkt')

_stemmer = PorterStemmer()


def tokenize(sentence: str) -> list[str]:
    """Split a sentence into word/punctuation tokens."""
    return nltk.word_tokenize(sentence)


def stem(word: str) -> str:
    """Return the Porter-stemmed lowercase root of a word."""
    return _stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence: list[str], vocabulary: list[str]) -> np.ndarray:
    """
    Build a binary bag-of-words vector.

    Args:
        tokenized_sentence: List of tokens from the user input.
        vocabulary:         Full sorted vocabulary from training.

    Returns:
        Float32 numpy array of shape (len(vocabulary),) with 1s for present words.

    Example:
        sentence  = ["hello", "how", "are", "you"]
        vocabulary = ["hi", "hello", "I", "you", "bye", "thank", "cool"]
        result    = [0, 1, 0, 1, 0, 0, 0]
    """
    stemmed = {stem(w) for w in tokenized_sentence}
    return np.array(
        [1.0 if w in stemmed else 0.0 for w in vocabulary],
        dtype=np.float32,
    )