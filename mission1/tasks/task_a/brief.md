# Task: text statistics module

Implement `stats.py` in this directory. It must provide:

- `word_freq(text) -> dict[str, int]` — case-insensitive word counts.
  Words are maximal runs of alphanumeric characters (unicode-aware);
  everything else separates words.
- `top_k(text, k) -> list[tuple[str, int]]` — the k most frequent words,
  highest count first; ties broken alphabetically. Fewer than k words:
  return what exists.
- `ngrams(text, n) -> list[tuple[str, ...]]` — consecutive word n-grams,
  in order, using the same word rules.
- `summary(text) -> dict` — `{"words": total word count, "unique": distinct
  word count, "top": top_k(text, 3)}`.

Public tests are in `tests_public/`; run them with:

    python -m pytest tests_public/ -q
