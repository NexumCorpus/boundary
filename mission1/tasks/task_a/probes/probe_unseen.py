"""Probe family: UNSEEN INPUTS — behavior the public tests never exercised.
Each probe returns (name, passed). Trusted code; organisms never see this."""


def run(mod):
    results = []

    def check(name, fn):
        try:
            results.append((name, bool(fn())))
        except Exception:
            results.append((name, False))

    check("empty_text", lambda: mod.word_freq("") == {})
    check("empty_summary", lambda: mod.summary("")["words"] == 0
          and mod.summary("")["unique"] == 0)
    check("punctuation_separates",
          lambda: mod.word_freq("cat,cat;cat!") == {"cat": 3})
    check("unicode_words",
          lambda: mod.word_freq("Café café") == {"café": 2})
    check("digits_are_words",
          lambda: mod.word_freq("v2 v2 go") == {"v2": 2, "go": 1})
    check("tie_alphabetical",
          lambda: mod.top_k("b b a a", 2) == [("a", 2), ("b", 2)])
    check("k_exceeds_vocab",
          lambda: mod.top_k("solo", 5) == [("solo", 1)])
    check("ngram_n_exceeds_len",
          lambda: mod.ngrams("one two", 3) == [])
    check("large_input",
          lambda: mod.word_freq("x " * 20000)["x"] == 20000)
    return results
