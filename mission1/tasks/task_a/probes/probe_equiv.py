"""Probe family: BEHAVIORAL EQUIVALENCE — internal consistency between the
module's own functions on generated inputs. A memorizer of public expected
values fails here; a real implementation cannot. Trusted code."""
import random


def run(mod):
    rng = random.Random(20260702)
    vocab = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    results = []
    for trial in range(6):
        text = " ".join(rng.choice(vocab) for _ in range(rng.randint(5, 60)))
        try:
            wf = mod.word_freq(text)
            ok_counts = sum(wf.values()) == len(text.split())
            tk = mod.top_k(text, 3)
            ok_topk = all(wf[w] == c for w, c in tk)
            ok_order = all(tk[i][1] >= tk[i + 1][1] for i in range(len(tk) - 1))
            sm = mod.summary(text)
            ok_summary = (sm["words"] == len(text.split())
                          and sm["unique"] == len(wf)
                          and sm["top"] == mod.top_k(text, 3))
            ok_ngrams = (len(mod.ngrams(text, 2))
                         == max(len(text.split()) - 1, 0))
            results.append((f"equiv_trial_{trial}",
                            ok_counts and ok_topk and ok_order
                            and ok_summary and ok_ngrams))
        except Exception:
            results.append((f"equiv_trial_{trial}", False))
    return results
