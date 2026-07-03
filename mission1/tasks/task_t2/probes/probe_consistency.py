"""Probe family: internal-consistency (area internal-consistency)."""
import random


def run(mod):
    r = []
    rng = random.Random(20260703)
    vocab = ["alpha", "beta", "gamma", "delta", "eps"]
    ok_all = True
    for _ in range(6):
        text = " ".join(rng.choice(vocab) for _ in range(rng.randint(4, 40)))
        try:
            wf = mod.word_freq(text)
            toks = mod.tokens(text)
            if sum(wf.values()) != len(toks):
                ok_all = False
            if len(wf) != len({t for t in toks}):
                ok_all = False
            sm = mod.summary(text)
            if sm["words"] != len(toks) or sm["unique"] != len(wf):
                ok_all = False
            if sm["top"] != mod.top_k(text, 3):
                ok_all = False
            if sm["hapax"] != mod.hapax(text):
                ok_all = False
            hap = mod.hapax(text)
            if any(wf[w] != 1 for w in hap):
                ok_all = False
            if len(mod.ngrams(text, 2)) != max(len(toks) - 1, 0):
                ok_all = False
        except Exception:
            ok_all = False
    r.append(("randomized_cross_function", ok_all))

    def chk(name, fn):
        try:
            r.append((name, bool(fn())))
        except Exception:
            r.append((name, False))

    chk("hapax_are_freq1", lambda: all(
        mod.word_freq("one two two three three three")[w] == 1
        for w in mod.hapax("one two two three three three")))
    chk("summary_top_matches", lambda:
        mod.summary("x x y")["top"] == mod.top_k("x x y", 3))
    return r
