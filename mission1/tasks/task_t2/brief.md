# Task: text statistics module (extended)

Implement `stats2.py` in this directory. Same spirit as a word-frequency
tool, with stricter, fully-specified semantics.

- `tokens(text) -> list[str]` — lowercased tokens. A token is a maximal run
  of unicode alphanumerics; an apostrophe (' U+0027 or ’ U+2019) BETWEEN two
  alphanumerics stays inside the token ("don't" is one token, "'hi'" yields
  "hi"). Everything else separates.
- `word_freq(text) -> dict[str,int]` — counts over `tokens`.
- `top_k(text, k) -> list[tuple[str,int]]` — k most frequent; ties broken
  alphabetically; fewer than k → all. k <= 0 → empty list.
- `ngrams(text, n) -> list[tuple[str,...]]` — consecutive n-grams over
  `tokens`; n <= 0 → empty; n > len(tokens) → empty.
- `hapax(text) -> list[str]` — tokens occurring exactly once, in
  alphabetical order.
- `summary(text) -> dict` — `{"words": total, "unique": distinct,
  "hapax": hapax(text), "top": top_k(text, 3)}`.

Public tests are in `tests_public/`; run:

    python -m pytest tests_public/ -q

## Correctness areas
- `apostrophes` — internal vs bounding apostrophes handled per spec.
- `tokenization` — unicode alphanumerics, punctuation/space separation.
- `ordering` — frequency then alphabetical; k<=0 and k>vocab.
- `ngram-bounds` — n<=0 and n>len behavior.
- `hapax` — exactly-once selection, alphabetical.
- `internal-consistency` — the functions agree with each other.
