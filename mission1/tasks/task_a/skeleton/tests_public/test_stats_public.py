import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stats import ngrams, summary, top_k, word_freq


def test_word_freq_basic():
    assert word_freq("the cat and the hat") == {
        "the": 2, "cat": 1, "and": 1, "hat": 1}


def test_word_freq_case_insensitive():
    assert word_freq("Dog dog DOG") == {"dog": 3}


def test_top_k_basic():
    assert top_k("a a a b b c", 2) == [("a", 3), ("b", 2)]


def test_ngrams_basic():
    assert ngrams("one two three", 2) == [("one", "two"), ("two", "three")]


def test_summary_basic():
    s = summary("red red blue")
    assert s["words"] == 3
    assert s["unique"] == 2
    assert s["top"][0] == ("red", 2)
