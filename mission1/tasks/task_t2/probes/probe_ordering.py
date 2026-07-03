"""Probe family: ordering (area ordering) + ngram bounds (area ngram-bounds)."""


def run(mod):
    r = []

    def chk(name, fn):
        try:
            r.append((name, bool(fn())))
        except Exception:
            r.append((name, False))

    chk("freq_then_alpha", lambda: mod.top_k("b b a a c", 3)
        == [("a", 2), ("b", 2), ("c", 1)])
    chk("k_zero_empty", lambda: mod.top_k("a a b", 0) == [])
    chk("k_negative_empty", lambda: mod.top_k("a a b", -1) == [])
    chk("k_exceeds_vocab", lambda: mod.top_k("solo", 9) == [("solo", 1)])
    chk("all_tie_alpha", lambda: mod.top_k("c b a", 3)
        == [("a", 1), ("b", 1), ("c", 1)])
    chk("ngram_n_zero", lambda: mod.ngrams("a b c", 0) == [])
    chk("ngram_n_negative", lambda: mod.ngrams("a b c", -2) == [])
    chk("ngram_n_exceeds", lambda: mod.ngrams("a b", 3) == [])
    chk("ngram_n_equals_len", lambda: mod.ngrams("a b", 2) == [("a", "b")])
    return r
