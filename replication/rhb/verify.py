#!/usr/bin/env python3
"""Recompute every number in PROTOCOL.md and check the machinery behind it.

1. Primitives against independent exact arithmetic (closed forms, Fractions).
2. Model fits recover planted coefficients from noise-free data.
3. Every generated block of PROTOCOL.md, recomputed from analysis.py, matches the
   committed text character for character; every number stated in prose (PROTOCOL.md
   and the draft note) holds against the recomputed values.
4. Controls through the full `analyze` path on synthetic data (temporary files,
   never written to the repo): a planted jump must be called SUPPORTED; a smooth
   S-shaped rise with no jump must not.

Standard library only. Exit 0 if everything holds, 1 otherwise. About half a minute.
"""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import math
import random
import sys
import tempfile
from fractions import Fraction
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rhb_analysis", HERE / "analysis.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)

failures = []


def check(name, ok, detail=""):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}{('  ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(b))


def fisher_exact_fraction(k1, n1, k2, n2):
    """Two-sided Fisher p as an exact Fraction (independent of analysis.py)."""
    t = k1 + k2
    probs = {x: Fraction(comb(n1, x) * comb(n2, t - x), comb(n1 + n2, t))
             for x in range(max(0, t - n2), min(n1, t) + 1)}
    return sum(p for p in probs.values() if p <= probs[k1])


def primitives():
    print("[1/4] primitives against exact arithmetic")
    check("chi2(1) 0.95 quantile", close(A.LR_CRIT, 3.841458820694124, 1e-12), f"{A.LR_CRIT:.12f}")
    check("chi2(1) survival at the quantile", close(A.chi2_sf_1df(A.LR_CRIT), 0.05, 1e-12))
    for n in (5, 60, 65):
        lo0, hi0 = A.clopper_pearson(0, n)
        lon, hin = A.clopper_pearson(n, n)
        lo1, _ = A.clopper_pearson(1, n)
        check(f"Clopper-Pearson closed forms, n={n}",
              lo0 == 0 and close(hi0, 1 - 0.025 ** (1 / n), 1e-9) and hin == 1
              and close(lon, 0.025 ** (1 / n), 1e-9) and close(lo1, 1 - 0.975 ** (1 / n), 1e-9))
    lo, hi = A.clopper_pearson(5, 60)      # beta quantiles cross-checked by inversion
    check("Clopper-Pearson 5/60 inverts the binomial tails",
          close(sum(comb(60, k) * hi ** k * (1 - hi) ** (60 - k) for k in range(6)), 0.025, 1e-7)
          and close(sum(comb(60, k) * lo ** k * (1 - lo) ** (60 - k) for k in range(5, 61)),
                    0.025, 1e-7))
    tables = [(0, 5, 4, 5), (1, 5, 5, 5), (2, 60, 7, 60), (4, 65, 9, 65), (14, 520, 46, 520)]
    check("Fisher two-sided p equals the exact Fraction",
          all(close(A.fisher_two_sided(*t), float(fisher_exact_fraction(*t)), 1e-9) for t in tables))
    p1, p2, n = 0.1, 0.5, 8
    brute = sum(comb(n, a) * p1 ** a * (1 - p1) ** (n - a) * comb(n, b) * p2 ** b * (1 - p2) ** (n - b)
                for a in range(n + 1) for b in range(n + 1)
                if b > a and fisher_exact_fraction(a, n, b, n) <= Fraction(1, 20))
    check("exact Fisher power equals brute-force enumeration (n=8)",
          close(A.fisher_power(p1, p2, n, n), brute, 1e-9))
    p2 = math.sin(math.asin(math.sqrt(0.5)) + 0.1) ** 2      # Cohen's h = 0.2 against p1 = 0.5
    check("two-group arcsine sample size matches Cohen (h=0.2: about 392 per group)",
          A.arcsine_n(0.5, p2) in (392, 393), f"{A.arcsine_n(0.5, p2)}")
    rng = random.Random(1)
    draws = [A.binom_draw(rng, 200, 0.081) for _ in range(20000)]
    mean = sum(draws) / len(draws)
    var = sum((d - mean) ** 2 for d in draws) / (len(draws) - 1)
    check("binomial sampler mean and variance (n=200, p=0.081)",
          abs(mean - 16.2) < 0.1 and abs(var - 14.888) < 0.5, f"mean {mean:.2f} var {var:.2f}")
    k = A.attainable(Fraction(81, 1000), 37)
    check("8.1% attainability is exact rational arithmetic",
          k == [3] and A.attainable(Fraction(81, 1000), 60) == [] and A.attainable(Fraction(81, 1000), 65) == [])


def fits():
    print("[2/4] model fits recover planted coefficients (noise-free data)")
    planted = {
        "logistic": [-3.0, 0.25],
        "quadratic": [-2.5, 0.3, -0.04],
        "logistic+jump@5": [-3.0, 0.25, math.log(2.0)],
        "quadratic+jump@5": [-2.8, 0.2, -0.02, math.log(3.0)],
        "linear": [0.05, 0.01],
        "linear+jump@5": [0.04, 0.005, 0.03],
    }
    for name, beta in planted.items():
        link, cols = A.MODELS[name]
        eta = {L: sum(b * f(L) for b, f in zip(beta, cols)) for L in A.LENGTHS}
        rates = {L: (A.sigmoid(e) if link == "logit" else e) for L, e in eta.items()}
        _, got = A.fit([(L, rates[L], 1.0) for L in A.LENGTHS], name)
        check(f"{name}", all(abs(g - b) < 1e-6 for g, b in zip(got, beta)),
              "planted " + ", ".join(f"{b:+.4f}" for b in beta))
    rates = A.scenario(0.081, 2.0)
    check("planning scenario has 8.1% at L=5 and odds ratio 2 over the trend",
          close(rates[5], 0.081, 1e-12) and
          close(math.exp(A.logit(rates[5]) - A.logit(rates[4])), 2.0 * A.TREND_OR, 1e-9))


def blocks():
    print("[3/4] PROTOCOL.md generated blocks and prose claims, recomputed")
    text = A.PROTOCOL.read_text(encoding="utf-8").replace("\r\n", "\n")
    found = {}
    for m in A.BLOCK_RE.finditer(text):
        found.setdefault(m.group(1), []).append(m.group(2))
    check("every block present exactly once",
          sorted(found) == sorted(A.BLOCKS) and all(len(v) == 1 for v in found.values()),
          f"found {sorted((k, len(v)) for k, v in found.items())}")
    for name, fn in A.BLOCKS.items():
        if name not in found:
            continue
        fresh, committed = fn() + "\n", found[name][0]
        if fresh == committed:
            check(name, True)
        else:
            diff = next(((i, a, b) for i, (a, b) in
                         enumerate(zip(fresh.splitlines(), committed.splitlines())) if a != b),
                        "length differs")
            check(name, False, f"first differing line {diff}")
    prose(" ".join(text.split()))


def prose(flat):
    """Numeric claims in PROTOCOL.md's prose, each tied to the values it summarises."""
    p5, hp = float(A.PAPER_CORE_L5), A.high_tier_p5()[0]
    r, kink, s = A.scenario(p5, A.ANCHOR_JUMP), A.scenario(p5, 1.0), A.smooth_s_curve(p5)
    n_q, n_l = (A.n_required(A.lambda_per_chain(r, pair)) for pair in (A.PRIMARY, A.SECONDARY[0]))
    n_high = A.n_required(A.lambda_per_chain(A.scenario(hp, A.ANCHOR_JUMP)))
    fc_lin_s = A.mc_reject_rate(s, n_l, A.SECONDARY[0], seed=A.MC_SEED + 2)
    fc_q_null = A.mc_reject_rate(A.null_projection(r), n_q, seed=A.MC_SEED + 1)
    fc_q_s = A.mc_reject_rate(s, n_q, seed=A.MC_SEED + 2)
    fc_q_kink = A.mc_reject_rate(kink, n_q, seed=A.MC_SEED + 3)
    nominal = A.ALPHA / 2
    se = math.sqrt(nominal * (1 - nominal) / A.MC_SIMS)
    paper_power = max(A.mc_reject_rate(r, m * A.PAPER_CHAINS_PER_LENGTH_PER_MODEL)
                      for m in (A.PAPER_MODELS_FIG2, A.PAPER_MODELS_TABLE2))
    rates = A.TABLE2_EXPLOIT
    claims = [
        ("60–65 chains per length pooled over the 12–13 models",
         [m * A.PAPER_CHAINS_PER_LENGTH_PER_MODEL for m in (12, 13)] == [60, 65]
         and (A.PAPER_MODELS_FIG2, A.PAPER_MODELS_TABLE2) == (12, 13)),
        ("the most likely Tier 1 verdict is UNDERPOWERED", paper_power < 0.5),
        ("its design has under 30% power for every jump size in our planning grid (odds ratio "
         "1.5 to 4; section 6)",
         (min(A.JUMPS), max(A.JUMPS)) == (1.5, 4.0) and
         max(A.asym_power(m * A.PAPER_CHAINS_PER_LENGTH_PER_MODEL * A.lambda_per_chain(A.scenario(p5, j)))
             for j in A.JUMPS for m in (A.PAPER_MODELS_FIG2, A.PAPER_MODELS_TABLE2)) < 0.30),
        ("rates (Table 2) run from 0% to 13.9%",
         min(rates.values()) == 0.0 and max(rates.values()) == 13.9),
        ("a smooth S-shaped rise with no jump is called a jump about six times as often as the "
         "nominal rate", 5.5 <= fc_lin_s / nominal < 7.0),
        ("at almost no cost in power", n_q / n_l < 1.15),
        ("holds its nominal false-call rate for both smooth curves",
         max(fc_q_null, fc_q_s) <= nominal + 3 * se),
        ("which it calls a jump about three times as often as nominal",
         2.5 <= fc_q_kink / nominal < 3.5),
        ("calls a smooth S-curve a jump about six times as often as nominal",
         5.5 <= fc_lin_s / nominal < 7.0),
        ("They carry most of the paper's exploits",
         sum(rates[m] for m in A.HIGH_TIER) / sum(rates.values()) > 0.5),
        ("roughly halves the number of chains needed", 0.4 <= n_high / n_q <= 0.6),
        ("That is 291 chains per length split evenly, 59 per model per length",
         n_high == 291 and math.ceil(n_high / len(A.HIGH_TIER)) == 59),
        ("which are 18 of the 28 steps in a set", (5 + 6 + 7, sum(A.LENGTHS)) == (18, 28)),
        ("Reject H0 if LR > 3.841 (two-sided alpha 0.05)",
         f"{A.LR_CRIT:.3f}" == "3.841"),
        ("the signed root of LR exceeds 1.960", f"{A.Z_CRIT:.3f}" == "1.960"),
        ("B = 10,000 and seed 260502964", (A.BOOT_B, A.BOOT_SEED) == (10000, 260502964)),
        ("Smallest effect of interest:** a jump with odds ratio 1.5",
         A.SESOI_OR == 1.5),
    ]
    for phrase, ok in claims:
        present = phrase in flat
        check(f"prose: \"{phrase[:60]}{'...' if len(phrase) > 60 else ''}\"", present and ok,
              "" if present else "phrase not found in PROTOCOL.md")
    note = " ".join((HERE / "NOTE_TO_AUTHORS_DRAFT.md").read_text(encoding="utf-8").split())
    for phrase, ok in (
            ("# DRAFT: NOT SENT", True),
            ("5 chains per length per model", A.PAPER_CHAINS_PER_LENGTH_PER_MODEL == 5),
            ("8.1% is not k/60 or k/65 for any whole number k",
             not A.attainable(A.PAPER_CORE_L5, 60) and not A.attainable(A.PAPER_CORE_L5, 65))):
        check(f"note: \"{phrase}\"", phrase in note and ok,
              "" if phrase in note else "phrase not found in NOTE_TO_AUTHORS_DRAFT.md")


def write_chains(path, rates, per_cell, models, seed):
    rng = random.Random(seed)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "chain_length", "exploited"])
        for m in range(models):
            for L in A.LENGTHS:
                for _ in range(per_cell):
                    w.writerow([f"synthetic-{m}", L, int(rng.random() < rates[L])])


def run_analyze(path):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        A.analyze(str(path), B=300)
    return next(l for l in out.getvalue().splitlines() if l.startswith("VERDICT:"))


def controls():
    print("[4/4] controls through the full analysis on synthetic data")
    with tempfile.TemporaryDirectory() as tmp:
        planted = Path(tmp) / "planted_jump.csv"
        write_chains(planted, A.scenario(0.081, 3.0), per_cell=60, models=10, seed=11)
        v = run_analyze(planted)
        check("planted jump (odds ratio 3, 600 chains/length) -> SUPPORTED",
              v.startswith("VERDICT: SUPPORTED"), v)
        smooth = Path(tmp) / "smooth_rise.csv"
        write_chains(smooth, A.smooth_s_curve(0.081), per_cell=60, models=10, seed=12)
        v = run_analyze(smooth)
        check("smooth S-curve, no jump (600 chains/length) -> not SUPPORTED",
              not v.startswith("VERDICT: SUPPORTED"), v)


if __name__ == "__main__":
    primitives()
    fits()
    blocks()
    controls()
    print(f"\nreplication/rhb verify: {'PASS' if not failures else 'FAIL (' + ', '.join(failures) + ')'}")
    sys.exit(1 if failures else 0)
