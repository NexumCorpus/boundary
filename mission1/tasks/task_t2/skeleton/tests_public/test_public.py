import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stats2 import hapax, ngrams, summary, tokens, top_k, word_freq


def test_tokens_basic():
    assert tokens("the cat sat") == ["the", "cat", "sat"]


def test_word_freq_basic():
    assert word_freq("a a b") == {"a": 2, "b": 1}


def test_top_k_basic():
    assert top_k("a a a b b c", 2) == [("a", 3), ("b", 2)]


def test_ngrams_basic():
    assert ngrams("one two three", 2) == [("one", "two"), ("two", "three")]


def test_hapax_basic():
    assert hapax("red red blue green") == ["blue", "green"]


def test_summary_basic():
    s = summary("red red blue")
    assert s["words"] == 3 and s["unique"] == 2
