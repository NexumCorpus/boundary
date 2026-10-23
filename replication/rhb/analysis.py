#!/usr/bin/env python3
"""RHB (arXiv 2605.02964) section 6.3: the "phase transition at chain length 5".

Preregistered analysis and power analysis for PROTOCOL.md. Standard library only
(the repo pins nothing but pytest), Python 3.9+.

  python analysis.py analyze CHAINS.csv [--independent STEPS.csv]
        run the preregistered analysis (PROTOCOL.md section 5) on per-chain records
  python analysis.py power
        print every generated block of PROTOCOL.md (power analysis, budget, checks)
  python analysis.py power --write
        refresh those blocks in PROTOCOL.md in place (verify.py checks they match)

No RHB data is read or shipped here: the per-instance records are not public
(PROTOCOL.md section 2). Every scenario rate below is an ASSUMPTION for planning,
labelled as such, never a result.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import re
from fractions import Fraction
from pathlib import Path
from statistics import NormalDist

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "PROTOCOL.md"

LENGTHS = (1, 2, 3, 4, 5, 6, 7)
CHANGE_AT = 5                      # the paper's step 5: first hidden-split step
ALPHA = 0.05                       # two-sided; only an upward jump counts (one-sided 0.025)
TARGET_POWER = 0.80
SESOI_OR = 1.5                     # smallest jump (odds ratio) a "not supported" verdict must exclude
N01 = NormalDist()
Z_CRIT = N01.inv_cdf(1 - ALPHA / 2)                         # 1.959964
LR_CRIT = Z_CRIT ** 2                                       # 3.841459, chi2(1) 0.95 quantile
LAMBDA_TARGET = (Z_CRIT + N01.inv_cdf(TARGET_POWER)) ** 2   # noncentrality for 80% power

# Numbers quoted from the paper (v1, the ICML 2026 camera-ready text).
PAPER_CHAINS_PER_LENGTH_PER_MODEL = 5          # section 5.4, "Sample size"
PAPER_MODELS_TABLE2 = 13                       # abstract, Table 2
PAPER_MODELS_FIG2 = 12                         # Figure 2 caption
PAPER_CORE_L5 = Fraction(81, 1000)             # 8.1%: sections 4.1 and 7 (CoreRHB, length 5)
PAPER_MICRO_L5 = Fraction(23, 1000)            # 2.3%: sections 4.1 and 7 (MicroRHB, length 5)
PAPER_COST_PER_EPISODE = (5, 50)               # USD, sections 5.4 and 8
TABLE2_EXPLOIT = {                             # standard-task exploit rate (%), Table 2
    "Claude Sonnet 4.5": 0.0, "Claude Opus 4.5": 0.0, "Claude 3.5 Sonnet v2": 0.6,
    "GPT-4o": 0.9, "Gemini 2.5 Flash Preview": 0.8, "DeepSeek-V3": 0.6,
    "Claude 3.7 Sonnet": 3.9, "Gemini 2.5 Pro Preview": 4.6, "o1": 6.8, "o3-mini": 7.1,
    "o4-mini": 8.4, "o3": 11.8, "DeepSeek-R1-Zero": 13.9,
}
HIGH_TIER = ("o1", "o3-mini", "o4-mini", "o3", "DeepSeek-R1-Zero")   # section 5.4, "High" tier

# Planning assumptions (PROTOCOL.md section 6). Not data.
TREND_OR = 1.3                     # per-step odds ratio before the jump ("increase moderately")
JUMPS = (1.5, 2.0, 3.0, 4.0)       # odds ratio at L=5 over the extrapolated trend
ANCHOR_JUMP = 2.0
MC_SIMS = 5000
MC_SEED = 20261023
BOOT_B = 10000
BOOT_SEED = 260502964


# ---------------------------------------------------------------- primitives

def log_sigmoid(x):
    return -math.log1p(math.exp(-x)) if x >= 0 else x - math.log1p(math.exp(x))


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x)) if x >= 0 else math.exp(x) / (1.0 + math.exp(x))


def logit(p):
    return math.log(p / (1.0 - p))


def log_choose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def chi2_sf_1df(x):
    return math.erfc(math.sqrt(max(x, 0.0) / 2.0))


def _betacf(a, b, x):
    """Continued fraction for the regularized incomplete beta (modified Lentz)."""
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1.0)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1000):
        m2 = 2 * m
        for num in (m * (b - m) * x / ((a + m2 - 1) * (a + m2)),
                    -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1))):
            d = 1.0 + num * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + num / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-15:
            break
    return h


def betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
           + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def beta_ppf(q, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def clopper_pearson(k, n, alpha=ALPHA):
    lo = 0.0 if k == 0 else beta_ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta_ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


def _hypergeom_pmfs(n1, n2, t):
    """P(X = x) for X successes in group 1, given t successes in total."""
    lo, hi = max(0, t - n2), min(n1, t)
    return lo, [math.exp(log_choose(n1, x) + log_choose(n2, t - x) - log_choose(n1 + n2, t))
                for x in range(lo, hi + 1)]


def fisher_two_sided(k1, n1, k2, n2):
    lo, pm = _hypergeom_pmfs(n1, n2, k1 + k2)
    obs = pm[k1 - lo]
    return min(1.0, sum(p for p in pm if p <= obs * (1 + 1e-7)))


def _binom_pmfs(n, p):
    return [math.exp(log_choose(n, k) + k * math.log(p) + (n - k) * math.log1p(-p))
            for k in range(n + 1)]


def fisher_power(p1, p2, n1, n2, alpha=ALPHA):
    """Exact power of the two-sided Fisher test, counting rejections with group 2 higher."""
    pvals = {}
    for t in range(n1 + n2 + 1):
        lo, pm = _hypergeom_pmfs(n1, n2, t)
        pvals[t] = (lo, [min(1.0, sum(q for q in pm if q <= p * (1 + 1e-7))) for p in pm])
    l1, l2 = _binom_pmfs(n1, p1), _binom_pmfs(n2, p2)
    power = 0.0
    for k1 in range(n1 + 1):
        for k2 in range(n2 + 1):
            lo, pv = pvals[k1 + k2]
            if k2 * n1 > k1 * n2 and pv[k1 - lo] <= alpha:
                power += l1[k1] * l2[k2]
    return power


def binom_draw(rng, n, p):
    """Binomial(n, p) by geometric skips: O(n p) uniforms, deterministic given rng."""
    if p <= 0.0:
        return 0
    if p >= 1.0:
        return n
    if p > 0.5:
        return n - binom_draw(rng, n, 1.0 - p)
    lq = math.log1p(-p)
    pos, x = 0, 0
    while True:
        pos += int(math.log(1.0 - rng.random()) / lq) + 1
        if pos > n:
            return x
        x += 1


def quantile(sorted_vals, q):
    """Linear interpolation between order statistics (Hyndman-Fan type 7)."""
    h = (len(sorted_vals) - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (h - lo) * (sorted_vals[hi] - sorted_vals[lo])


def _solve(a, b):
    """Gaussian elimination with partial pivoting."""
    k = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(k):
        piv = max(range(c, k), key=lambda r: abs(m[r][c]))
        m[c], m[piv] = m[piv], m[c]
        if abs(m[c][c]) < 1e-300:
            m[c][c] = 1e-300
        for r in range(c + 1, k):
            f = m[r][c] / m[c][c]
            for j in range(c, k + 1):
                m[r][j] -= f * m[c][j]
    x = [0.0] * k
    for r in range(k - 1, -1, -1):
        x[r] = (m[r][k] - sum(m[r][j] * x[j] for j in range(r + 1, k))) / m[r][r]
    return x


# ------------------------------------------------------------ binomial models
# cells: list of (L, k, n); k and n may be fractional (exemplary data for power).

def one(L):
    return 1.0


def lin(L):
    return float(L - 4)


def quad(L):
    return float((L - 4) ** 2)


def ind(tau):
    return lambda L: 1.0 if L >= tau else 0.0


def _ll_logit(cells, X, beta, off):
    s = 0.0
    for (L, k, n), x, o in zip(cells, X, off):
        eta = o + sum(b * v for b, v in zip(beta, x))
        s += k * log_sigmoid(eta) + (n - k) * log_sigmoid(-eta)
    return s


def fit_logit(cells, cols, offset=None):
    """Binomial GLM, logit link, Newton-Raphson with step halving. Returns (loglik, beta).

    Under separation (all-zero cells) coefficients drift but the log-likelihood
    converges to its supremum, which is all the likelihood-ratio tests need.
    """
    X = [[f(L) for f in cols] for L, _, _ in cells]
    off = [offset(L) if offset else 0.0 for L, _, _ in cells]
    tk, tn = sum(c[1] for c in cells), sum(c[2] for c in cells)
    start = logit(min(max(tk / tn, 1e-6), 1 - 1e-6))
    return fit_logit_X(cells, X, off, [start] + [0.0] * (len(cols) - 1))


def fit_logit_X(cells, X, off, beta):
    """Newton-Raphson on an explicit design matrix X (one row per cell)."""
    p_ = len(beta)
    ll = _ll_logit(cells, X, beta, off)
    for _ in range(300):
        g = [0.0] * p_
        H = [[1e-10 if i == j else 0.0 for j in range(p_)] for i in range(p_)]
        for (L, k, n), x, o in zip(cells, X, off):
            p = sigmoid(o + sum(b * v for b, v in zip(beta, x)))
            w = n * p * (1 - p)
            for i in range(p_):
                if x[i] == 0.0:
                    continue
                g[i] += x[i] * (k - n * p)
                for j in range(p_):
                    H[i][j] += x[i] * x[j] * w
        d = _solve(H, g)
        t = 1.0
        while True:
            cand = [b + t * di for b, di in zip(beta, d)]
            new = _ll_logit(cells, X, cand, off)
            if new >= ll or t < 1e-10:
                break
            t /= 2
        if new < ll:
            break
        gain, beta, ll = new - ll, cand, new
        if gain < 1e-11:
            break
    return ll, beta


EPS = 1e-9


def _ll_ident(cells, X, beta):
    s = 0.0
    for (L, k, n), x in zip(cells, X):
        p = sum(b * v for b, v in zip(beta, x))
        if not EPS / 2 <= p <= 1 - EPS / 2:
            return -math.inf
        s += k * math.log(p) + (n - k) * math.log1p(-p)
    return s


def fit_identity(cells, cols):
    """Linear probability model: binomial likelihood, p kept inside (0, 1)."""
    X = [[f(L) for f in cols] for L, _, _ in cells]
    tk, tn = sum(c[1] for c in cells), sum(c[2] for c in cells)
    beta = [min(max(tk / tn, 0.01), 0.99)] + [0.0] * (len(cols) - 1)
    ll = _ll_ident(cells, X, beta)
    for _ in range(500):
        g = [0.0] * len(cols)
        H = [[1e-10 if i == j else 0.0 for j in range(len(cols))] for i in range(len(cols))]
        for (L, k, n), x in zip(cells, X):
            p = sum(b * v for b, v in zip(beta, x))
            gs = k / p - (n - k) / (1 - p)
            hs = k / p ** 2 + (n - k) / (1 - p) ** 2
            for i in range(len(cols)):
                g[i] += x[i] * gs
                for j in range(len(cols)):
                    H[i][j] += x[i] * x[j] * hs
        d = _solve(H, g)
        t = 1.0
        while True:
            cand = [b + t * di for b, di in zip(beta, d)]
            new = _ll_ident(cells, X, cand)
            if new >= ll or t < 1e-12:
                break
            t /= 2
        if new < ll:
            break
        gain, beta, ll = new - ll, cand, new
        if gain < 1e-11:
            break
    return ll, beta


# name: (link, columns). In every "+jump@5" model the jump is the LAST coefficient.
MODELS = {
    "constant":          ("logit", [one]),
    "linear":            ("identity", [one, lin]),
    "logistic":          ("logit", [one, lin]),
    "quadratic":         ("logit", [one, lin, quad]),
    "step@5":            ("logit", [one, ind(CHANGE_AT)]),
    "linear+jump@5":     ("identity", [one, lin, ind(CHANGE_AT)]),
    "logistic+jump@5":   ("logit", [one, lin, ind(CHANGE_AT)]),
    "quadratic+jump@5":  ("logit", [one, lin, quad, ind(CHANGE_AT)]),
}
PRIMARY = ("quadratic", "quadratic+jump@5")      # H1, PROTOCOL.md section 5.2
SECONDARY = (("logistic", "logistic+jump@5"), ("linear", "linear+jump@5"))


def fit(cells, name):
    link, cols = MODELS[name]
    return (fit_logit if link == "logit" else fit_identity)(cells, cols)


def jump_test(cells, pair=PRIMARY):
    """Returns (signed root LR, LR, chi2(1) p, jump estimate) for null vs null+jump@5."""
    ll0, _ = fit(cells, pair[0])
    ll1, b1 = fit(cells, pair[1])
    lr = max(0.0, 2 * (ll1 - ll0))
    return math.copysign(math.sqrt(lr), b1[-1]), lr, chi2_sf_1df(lr), b1[-1]


def rejects(t):
    return t > Z_CRIT


# ------------------------------------------------------- planning scenarios

def scenario(p5, jump, trend_or=TREND_OR):
    """Assumed pooled exploit rate by chain length (planning only, not data).

    Logit-linear rise with per-step odds ratio `trend_or` up to L=4, an extra odds
    ratio `jump` at L=5 on top of the extrapolated trend, then a plateau at L=6-7
    (the paper: "plateau or slightly taper"). Scaled so that p(5) = p5. With
    jump = 1 the curve rises to L=5 and then flattens: a slope change, no jump.
    """
    l4 = logit(p5) - math.log(trend_or) - math.log(jump)
    return {L: (sigmoid(l4 + math.log(trend_or) * (L - 4)) if L <= 4 else p5) for L in LENGTHS}


def smooth_s_curve(p5):
    """A smooth S-shaped rise centred between L=4 and L=5, no jump: c * expit(L - 4.5)."""
    c = p5 / sigmoid(0.5)
    return {L: c * sigmoid(L - 4.5) for L in LENGTHS}


def null_projection(rates, pair=PRIMARY):
    """Closest curve in the test's smooth null family (KL projection)."""
    _, b = fit([(L, rates[L], 1.0) for L in LENGTHS], pair[0])
    cols = MODELS[pair[0]][1]
    if MODELS[pair[0]][0] == "identity":
        return {L: sum(bi * f(L) for bi, f in zip(b, cols)) for L in LENGTHS}
    return {L: sigmoid(sum(bi * f(L) for bi, f in zip(b, cols))) for L in LENGTHS}


def high_tier_p5():
    """Planning rate at L=5 for the high-tier models: 8.1% scaled by Table 2 rates."""
    allm = sum(TABLE2_EXPLOIT.values()) / len(TABLE2_EXPLOIT)
    high = sum(TABLE2_EXPLOIT[m] for m in HIGH_TIER) / len(HIGH_TIER)
    return round(float(PAPER_CORE_L5) * high / allm, 3), allm, high


def lambda_per_chain(rates, pair=PRIMARY):
    """Exemplary-data noncentrality of the jump test, per chain at each length."""
    cells = [(L, rates[L], 1.0) for L in LENGTHS]
    ll0, _ = fit(cells, pair[0])
    ll1, _ = fit(cells, pair[1])
    return max(0.0, 2 * (ll1 - ll0))


def asym_power(lam):
    return N01.cdf(math.sqrt(lam) - Z_CRIT)


def n_required(lam1):
    return math.ceil(LAMBDA_TARGET / lam1)


_MC_MEMO = {}


def mc_reject_rate(rates, n, pair=PRIMARY, sims=MC_SIMS, seed=MC_SEED):
    key = (tuple(rates[L] for L in LENGTHS), n, pair, sims, seed)
    if key not in _MC_MEMO:
        rng = random.Random(seed)
        hits = 0
        for _ in range(sims):
            cells = [(L, binom_draw(rng, n, rates[L]), n) for L in LENGTHS]
            hits += rejects(jump_test(cells, pair)[0])
        _MC_MEMO[key] = hits / sims
    return _MC_MEMO[key]


def arcsine_n(p1, p2):
    """Chains per group for two independent groups (Cohen's h): n = 2 ((z + z_power) / h)^2."""
    h = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))
    return math.ceil(2 * ((Z_CRIT + N01.inv_cdf(TARGET_POWER)) / h) ** 2)


def p_strictly_higher(n, p_lo, p_hi):
    """P(Bin(n, p_hi) > Bin(n, p_lo)), exact."""
    a, b = _binom_pmfs(n, p_lo), _binom_pmfs(n, p_hi)
    return sum(a[i] * sum(b[i + 1:]) for i in range(n + 1))


# ------------------------------------------------------------ generated blocks

def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def block_headline():
    lo_usd, hi_usd = PAPER_COST_PER_EPISODE
    r = scenario(float(PAPER_CORE_L5), ANCHOR_JUMP)
    hp, _, _ = high_tier_p5()
    lam1 = lambda_per_chain(r)
    ns = [m * PAPER_CHAINS_PER_LENGTH_PER_MODEL for m in (PAPER_MODELS_FIG2, PAPER_MODELS_TABLE2)]
    mc = [mc_reject_rate(r, n) for n in ns]
    n_all, n_high = n_required(lam1), n_required(lambda_per_chain(scenario(hp, ANCHOR_JUMP)))
    s_all, s_high = n_all * sum(LENGTHS), n_high * sum(LENGTHS)
    return (f"- The paper's design has {ns[0]}-{ns[1]} chains per length when pooled over "
            f"models. Under a planning scenario built from the paper's own description "
            f"(8.1% at L=5, odds of exploiting doubling at L=5 on top of a moderate trend), "
            f"the primary test detects the jump {pct(min(mc))}-{pct(max(mc))} of the time "
            f"(Monte Carlo).\n"
            f"- 80% power at alpha {ALPHA:g} needs about {n_all:,} chains per length at the "
            f"paper's average rates, or {n_high:,} if only the five high-tier models are run: "
            f"{s_all:,} or {s_high:,} single-step episodes, ${s_all * lo_usd:,}-"
            f"${s_all * hi_usd:,} or ${s_high * lo_usd:,}-${s_high * hi_usd:,} at the paper's "
            f"${lo_usd}-${hi_usd} per episode.\n"
            f"- One model's curve rests on {PAPER_CHAINS_PER_LENGTH_PER_MODEL} chains per point; "
            f"its L=4 -> L=5 rise reaches Fisher p < {ALPHA:g} only for "
            f"{', '.join(single_model_hits())}.")


def block_scenarios():
    hp, allm, high = high_tier_p5()
    out = [f"| planning scenario (jump odds ratio {ANCHOR_JUMP:g}, trend {TREND_OR:g}/step) | " +
           " | ".join(f"L={L}" for L in LENGTHS) + " |", "|---|" + "---|" * len(LENGTHS)]
    for label, p5 in (("MicroRHB rate (2.3% at L=5)", float(PAPER_MICRO_L5)),
                      ("CoreRHB rate (8.1% at L=5)", float(PAPER_CORE_L5)),
                      ("high-tier models only (derived)", hp)):
        r = scenario(p5, ANCHOR_JUMP)
        out.append(f"| {label} | " + " | ".join(pct(r[L]) for L in LENGTHS) + " |")
    out.append("")
    out.append(f"High-tier rate at L=5 = 8.1% x (mean Table 2 rate of {', '.join(HIGH_TIER)}: "
               f"{high:.2f}%) / (mean over all 13 models: {allm:.2f}%) = {pct(hp)}.")
    return "\n".join(out)


def block_paper_design():
    r = scenario(float(PAPER_CORE_L5), ANCHOR_JUMP)
    lam1 = lambda_per_chain(r)
    out = ["| chains per length (pooled over models) | primary test, asymptotic power | "
           "primary test, Monte Carlo power | Fisher L=4 vs L=5, exact power |",
           "|---|---|---|---|"]
    for m in (PAPER_MODELS_FIG2, PAPER_MODELS_TABLE2):
        n = m * PAPER_CHAINS_PER_LENGTH_PER_MODEL
        out.append(f"| {n} ({m} models x {PAPER_CHAINS_PER_LENGTH_PER_MODEL}) | "
                   f"{pct(asym_power(n * lam1))} | {pct(mc_reject_rate(r, n))} | "
                   f"{pct(fisher_power(r[4], r[5], n, n))} |")
    out.append("")
    out.append(f"Scenario: the CoreRHB row above (8.1% at L=5, jump odds ratio {ANCHOR_JUMP:g}). "
               f"Monte Carlo: {MC_SIMS} simulated data sets, seed {MC_SEED}.")
    return "\n".join(out)


def block_power_grid():
    hp, _, _ = high_tier_p5()
    out = ["| rate at L=5 | jump odds ratio | implied rate at L=4 | power at 60 chains/length "
           "| chains/length for 80% power | chains in total (x7) |", "|---|---|---|---|---|---|"]
    for p5 in (float(PAPER_MICRO_L5), float(PAPER_CORE_L5), hp):
        for j in JUMPS:
            r = scenario(p5, j)
            lam1 = lambda_per_chain(r)
            n = n_required(lam1)
            out.append(f"| {pct(p5)} | {j:g} | {pct(r[4])} | {pct(asym_power(60 * lam1))} | "
                       f"{n:,} | {7 * n:,} |")
    out.append("")
    out.append(f"Asymptotic (exemplary-data) power of the primary test: two-sided alpha "
               f"{ALPHA:g}, upward jumps only, target power {TARGET_POWER:.0%} (noncentrality "
               f"{LAMBDA_TARGET:.3f}). Trend before the jump: odds ratio {TREND_OR:g} per step. "
               f"Lengths 1-7, equal chains per length, pooled over models.")
    return "\n".join(out)


def block_trend_sensitivity():
    out = ["| trend odds ratio per step before L=5 | chains/length for 80% power |", "|---|---|"]
    for tr in (1.0, 1.15, TREND_OR, 1.5):
        out.append(f"| {tr:g} | "
                   f"{n_required(lambda_per_chain(scenario(float(PAPER_CORE_L5), ANCHOR_JUMP, tr))):,} |")
    out.append("")
    out.append(f"CoreRHB rate (8.1% at L=5), jump odds ratio {ANCHOR_JUMP:g}.")
    return "\n".join(out)


def block_mc_check():
    p5 = float(PAPER_CORE_L5)
    r, kink, s = scenario(p5, ANCHOR_JUMP), scenario(p5, 1.0), smooth_s_curve(p5)
    out = ["| jump test, smooth null | chains/length for 80% | power (jump 2) | "
           "false calls: data from the null itself | false calls: smooth S-curve | "
           "false calls: rise then flat at L=5 |", "|---|---|---|---|---|---|"]
    for label, pair in (("primary: logit-quadratic", PRIMARY),
                        ("S1a: logit-linear (smooth logistic)", SECONDARY[0])):
        n = n_required(lambda_per_chain(r, pair))
        out.append(f"| {label} | {n:,} | {pct(mc_reject_rate(r, n, pair))} | "
                   f"{pct(mc_reject_rate(null_projection(r, pair), n, pair, seed=MC_SEED + 1))} | "
                   f"{pct(mc_reject_rate(s, n, pair, seed=MC_SEED + 2))} | "
                   f"{pct(mc_reject_rate(kink, n, pair, seed=MC_SEED + 3))} |")
    out.append("")
    se = [100 * math.sqrt(q * (1 - q) / MC_SIMS) for q in (TARGET_POWER, ALPHA / 2)]
    out.append(f"Monte Carlo, {MC_SIMS} data sets per cell (standard error about {se[0]:.1f} "
               f"points at {TARGET_POWER:.0%} and {se[1]:.1f} points at {ALPHA / 2:.1%}). A false call is a rejection with an upward jump "
               f"when there is none; the nominal rate is {ALPHA / 2:.1%}. Smooth S-curve: "
               f"{', '.join(pct(s[L]) for L in LENGTHS)} for L=1-7. Rise then flat: "
               f"{', '.join(pct(kink[L]) for L in LENGTHS)}.")
    return "\n".join(out)


def block_fisher():
    hp, _, _ = high_tier_p5()
    out = ["| scenario | rate L=4 -> L=5 | chains per length for 80% (arcsine) | "
           "exact Fisher power at that n |", "|---|---|---|---|"]
    for label, p5 in (("CoreRHB rate", float(PAPER_CORE_L5)), ("high-tier models", hp)):
        r = scenario(p5, ANCHOR_JUMP)
        n = arcsine_n(r[4], r[5])
        out.append(f"| {label} | {pct(r[4])} -> {pct(r[5])} | {n:,} | "
                   f"{pct(fisher_power(r[4], r[5], n, n))} |")
    return "\n".join(out)


def single_model_hits():
    n = PAPER_CHAINS_PER_LENGTH_PER_MODEL
    return [f"{a}/{n} -> {b}/{n}" for a in range(n + 1) for b in range(n + 1)
            if b > a and fisher_two_sided(a, n, b, n) < ALPHA]


def block_single_model():
    n = PAPER_CHAINS_PER_LENGTH_PER_MODEL
    lo, hi = clopper_pearson(0, n)
    lo1, hi1 = clopper_pearson(1, n)
    return (f"With {n} chains per length, the only L=4 -> L=5 outcomes with Fisher "
            f"p < {ALPHA:g} are " + ", ".join(single_model_hits()) +
            f". A single model's curve can take only the values 0, 20, 40, 60, 80 and 100%. "
            f"95% Clopper-Pearson intervals: 0/{n} is [{pct(lo)}, {pct(hi)}], "
            f"1/{n} is [{pct(lo1)}, {pct(hi1)}].")


def block_families():
    m = PAPER_MODELS_FIG2 * PAPER_CHAINS_PER_LENGTH_PER_MODEL // 4
    r, flat = scenario(float(PAPER_CORE_L5), ANCHOR_JUMP), scenario(float(PAPER_CORE_L5), 1.0)
    pj, pf = p_strictly_higher(m, r[4], r[5]), p_strictly_higher(m, flat[4], flat[5])
    return (f"About {m} chains per family per length ({PAPER_MODELS_FIG2} models x "
            f"{PAPER_CHAINS_PER_LENGTH_PER_MODEL} chains / 4 families, if balanced). "
            f"Probability that all four families show more exploits at L=5 than at L=4: "
            f"{pct(pj ** 4)} if the jump (odds ratio {ANCHOR_JUMP:g}) is real, {pct(pf ** 4)} "
            f"with the trend alone (per family: {pct(pj)} and {pct(pf)}). Families treated "
            f"as independent with equal rates.")


def attainable(target, n):
    """Integers k with 100 k / n rounding (half up) to `target` percent at 0.1."""
    lo, hi = 100 * target - Fraction(1, 20), 100 * target + Fraction(1, 20)
    return [k for k in range(n + 1) if lo <= Fraction(100 * k, n) < hi]


def block_consistency():
    out = []
    for m in (PAPER_MODELS_FIG2, PAPER_MODELS_TABLE2):
        n = m * PAPER_CHAINS_PER_LENGTH_PER_MODEL
        if attainable(PAPER_CORE_L5, n):
            out.append(f"- N = {n}: attainable")
            continue
        near = sorted(sorted(range(n + 1), key=lambda k: abs(Fraction(k, n) - PAPER_CORE_L5))[:2])
        out.append(f"- N = {n} ({m} models x {PAPER_CHAINS_PER_LENGTH_PER_MODEL}): no integer k "
                   f"gives 8.1%; nearest " + " and ".join(f"{k}/{n} = {100 * k / n:.2f}%"
                                                          for k in near))
    first = next(n for n in range(1, 1000) if attainable(PAPER_CORE_L5, n))
    out.append(f"- Smallest N for which some k/N rounds to 8.1%: {first} "
               f"({attainable(PAPER_CORE_L5, first)[0]}/{first}).")
    return "\n".join(out)


def block_budget():
    lo_usd, hi_usd = PAPER_COST_PER_EPISODE
    steps_per_n = sum(LENGTHS)
    hp, _, _ = high_tier_p5()
    rows = [("Paper as run (13 models x 5 chains per length)",
             PAPER_MODELS_TABLE2 * PAPER_CHAINS_PER_LENGTH_PER_MODEL)]
    for label, p5 in (("New data, all-model rates (8.1% at L=5)", float(PAPER_CORE_L5)),
                      ("New data, high-tier models only (17.0% at L=5)", hp)):
        rows.append((label, n_required(lambda_per_chain(scenario(p5, ANCHOR_JUMP)))))
    out = ["| option | chains per length | chains | step-episodes | cost at $5-$50 per step |",
           "|---|---|---|---|---|",
           "| Tier 1: re-analysis of the authors' records | as recorded | 0 new | 0 new | $0 |"]
    for label, n in rows:
        steps = n * steps_per_n
        out.append(f"| {label} | {n:,} | {n * len(LENGTHS):,} | {steps:,} | "
                   f"${steps * lo_usd:,} - ${steps * hi_usd:,} |")
    out.append("")
    out.append(f"Assumes a chain of length L costs L single-step episodes at the paper's "
               f"$5-$50 per episode. New-data rows: jump odds ratio {ANCHOR_JUMP:g}, 80% power, "
               f"lengths 1-7 ({steps_per_n} steps per chain-set).")
    return "\n".join(out)


BLOCKS = {
    "headline": block_headline,
    "scenarios": block_scenarios,
    "paper-design": block_paper_design,
    "power-grid": block_power_grid,
    "trend-sensitivity": block_trend_sensitivity,
    "mc-check": block_mc_check,
    "fisher": block_fisher,
    "single-model": block_single_model,
    "families": block_families,
    "consistency": block_consistency,
    "budget": block_budget,
}

BLOCK_RE = re.compile(r"<!-- generated:([a-z-]+) -->\n(.*?)<!-- /generated -->", re.S)


def render_block(name):
    return f"<!-- generated:{name} -->\n{BLOCKS[name]()}\n<!-- /generated -->"


def render_protocol(text):
    return BLOCK_RE.sub(lambda m: render_block(m.group(1)), text)


# ------------------------------------------------------- the analysis itself

def read_chains(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            first = (r.get("first_exploit_step") or "").strip()
            rows.append({"model": r["model"].strip(), "L": int(r["chain_length"]),
                         "x": int(r["exploited"]), "first": int(first) if first else None,
                         "family": (r.get("family") or "").strip()})
    bad = [r for r in rows if r["x"] not in (0, 1) or r["L"] not in LENGTHS]
    if bad:
        raise SystemExit(f"{len(bad)} rows with exploited not in {{0,1}} or length not in 1-7")
    return rows


def cells_from(rows):
    out = []
    for L in sorted({r["L"] for r in rows}):
        xs = [r["x"] for r in rows if r["L"] == L]
        out.append((L, sum(xs), len(xs)))
    return out


def bootstrap_ci(rows, B=BOOT_B, seed=BOOT_SEED):
    """Per-length 95% percentile intervals: resampling chains within each model x length
    cell, and resampling whole models (the between-model variance the pooled rate hides)."""
    rng = random.Random(seed)
    models = sorted({r["model"] for r in rows})
    lengths = sorted({r["L"] for r in rows})
    cell = {(m, L): [0, 0] for m in models for L in lengths}
    for r in rows:
        cell[(r["model"], r["L"])][0] += r["x"]
        cell[(r["model"], r["L"])][1] += 1
    within = {L: [] for L in lengths}
    clustered = {L: [] for L in lengths}
    for _ in range(B):
        for L in lengths:
            k = n = 0
            for m in models:
                ck, cn = cell[(m, L)]
                if cn:
                    k += binom_draw(rng, cn, ck / cn)
                    n += cn
            within[L].append(k / n)
        pick = [models[rng.randrange(len(models))] for _ in models]
        for L in lengths:
            k = sum(cell[(m, L)][0] for m in pick)
            n = sum(cell[(m, L)][1] for m in pick)
            if n:
                clustered[L].append(k / n)
    res = {}
    for L in lengths:
        w, c = sorted(within[L]), sorted(clustered[L])
        res[L] = ((quantile(w, 0.025), quantile(w, 0.975)), (quantile(c, 0.025), quantile(c, 0.975)))
    return res


def model_table(cells):
    """All models of section 5.3: log-likelihood (with binomial constants), AIC, BIC."""
    N = sum(c[2] for c in cells)
    const = sum(log_choose(n, k) for _, k, n in cells)
    rows = [(name, len(cols), fit(cells, name)[0] + const) for name, (_, cols) in MODELS.items()]
    taus = range(min(c[0] for c in cells) + 1, max(c[0] for c in cells) + 1)
    tau, ll = max(((t, fit_logit(cells, [one, ind(t)])[0]) for t in taus), key=lambda v: v[1])
    rows.append((f"step@free (best tau={tau})", 3, ll + const))
    sat = sum(k * math.log(k / n) + (n - k) * math.log1p(-k / n) for _, k, n in cells if 0 < k < n)
    table = [(name, p, ll, 2 * p - 2 * ll, p * math.log(N) - 2 * ll) for name, p, ll in rows]
    amin = min(t[3] for t in table)
    w = [math.exp(-(t[3] - amin) / 2) for t in table]
    table.append(("saturated (reference)", len(cells), sat + const,
                  2 * len(cells) - 2 * (sat + const), len(cells) * math.log(N) - 2 * (sat + const)))
    return table, [v / sum(w) for v in w] + [None], tau


def parametric_bootstrap_p(cells, t_obs, B=2000, seed=BOOT_SEED + 1):
    """One-sided p for the primary signed-root statistic under the fitted smooth null."""
    _, b = fit(cells, PRIMARY[0])
    cols = MODELS[PRIMARY[0]][1]
    rng = random.Random(seed)
    ge = 0
    for _ in range(B):
        sim = [(L, binom_draw(rng, n, sigmoid(sum(bi * f(L) for bi, f in zip(b, cols)))), n)
               for L, _, n in cells]
        ge += jump_test(sim)[0] >= t_obs - 1e-12
    return (1 + ge) / (B + 1)


def jump_profile_ci(cells, pair=PRIMARY):
    """95% profile-likelihood interval for the jump coefficient (logit models)."""
    cols = MODELS[pair[1]][1]
    ll1, b1 = fit(cells, pair[1])
    step = cols[-1]

    def deficit(d):
        ll, _ = fit_logit(cells, cols[:-1], offset=lambda L: d * step(L))
        return 2 * (ll1 - ll)

    def edge(sign):
        inside, out = b1[-1], b1[-1] + sign * 0.5
        while deficit(out) < LR_CRIT:
            out += sign * 0.5
            if abs(out - b1[-1]) > 30:
                return sign * math.inf
        for _ in range(60):
            mid = (inside + out) / 2
            if deficit(mid) < LR_CRIT:
                inside = mid
            else:
                out = mid
        return (inside + out) / 2
    return edge(-1), edge(+1)


def fixed_effects_test(rows):
    """S7: the primary test with one intercept per model (models with no exploits at
    all carry no information about the shape and are left out)."""
    models = sorted({r["model"] for r in rows if r["x"]})
    cells, X0 = [], []
    for i, m in enumerate(models):
        for L in sorted({r["L"] for r in rows if r["model"] == m}):
            xs = [r["x"] for r in rows if r["model"] == m and r["L"] == L]
            cells.append((L, sum(xs), len(xs)))
            X0.append([1.0 if j == i else 0.0 for j in range(len(models))] + [lin(L), quad(L)])
    if len(models) < 1 or len({c[0] for c in cells}) < 5:
        return None
    zero = [0.0] * len(cells)
    start = [logit(max(sum(c[1] for c in cells) / sum(c[2] for c in cells), 1e-6))] * len(models)
    ll0, _ = fit_logit_X(cells, X0, zero, start + [0.0, 0.0])
    X1 = [x + [ind(CHANGE_AT)(c[0])] for x, c in zip(X0, cells)]
    ll1, b1 = fit_logit_X(cells, X1, zero, start + [0.0, 0.0, 0.0])
    lr = max(0.0, 2 * (ll1 - ll0))
    return len(models), b1[-1], lr, chi2_sf_1df(lr)


def per_family(rows, families):
    out = []
    for fam in sorted(set(families.values())):
        cnt = {}
        for i, r in enumerate(rows):
            if families.get(i) == fam and r["L"] in (4, 5):
                cnt.setdefault(r["L"], [0, 0])
                cnt[r["L"]][0] += r["x"]
                cnt[r["L"]][1] += 1
        if 4 in cnt and 5 in cnt:
            out.append((fam, cnt[4], cnt[5], fisher_two_sided(*cnt[4], *cnt[5])))
    return out


def verdict(t, p_boot, jump_hi):
    """PROTOCOL.md section 5.4, applied mechanically."""
    if rejects(t) and p_boot < ALPHA / 2:
        return "SUPPORTED: a jump at L=5 beyond a smooth (logit-quadratic) trend"
    if rejects(t):
        return "INCONCLUSIVE: the chi-square test rejects but the parametric bootstrap does not"
    if jump_hi < math.log(SESOI_OR):
        return f"NOT SUPPORTED: the data exclude a jump of odds ratio {SESOI_OR:g} or more"
    return (f"UNDERPOWERED: no jump detected, and a jump of odds ratio {SESOI_OR:g} or more "
            f"is not excluded")


def analyze(chains_path, independent_path=None, B=BOOT_B):
    rows = read_chains(chains_path)
    cells = cells_from(rows)
    models = sorted({r["model"] for r in rows})
    print(f"# RHB section 6.3 re-analysis: {len(rows)} chains, {len(models)} models")

    print("\n## Exploit rate by chain length (95% intervals)\n")
    ci = bootstrap_ci(rows, B=B)
    print("| L | k/n | rate | Clopper-Pearson | bootstrap within cells | bootstrap over models |")
    print("|---|---|---|---|---|---|")
    for L, k, n in cells:
        lo, hi = clopper_pearson(k, n)
        (wl, wh), (cl, ch) = ci[L]
        print(f"| {L} | {k}/{n} | {pct(k / n)} | [{pct(lo)}, {pct(hi)}] | "
              f"[{pct(wl)}, {pct(wh)}] | [{pct(cl)}, {pct(ch)}] |")

    print("\n## Model comparison\n")
    table, w, tau = model_table(cells)
    print("| model | parameters | log-likelihood | AIC | BIC | Akaike weight |")
    print("|---|---|---|---|---|---|")
    for (name, p, ll, aic, bic), wt in zip(table, w):
        print(f"| {name} | {p} | {ll:.3f} | {aic:.2f} | {bic:.2f} | "
              f"{'' if wt is None else f'{wt:.3f}'} |")

    print("\n## Tests\n")
    t, lr, p_chi, jump = jump_test(cells)
    lo, hi = jump_profile_ci(cells)
    p_boot = parametric_bootstrap_p(cells, t, B=min(B, 2000))
    print(f"- H1 (quadratic+jump@5 vs quadratic): jump {jump:+.3f} on the logit scale (odds "
          f"ratio {math.exp(jump):.2f}), 95% profile CI [{lo:+.3f}, {hi:+.3f}]; LR {lr:.3f}, "
          f"signed root {t:+.3f}, chi2(1) p = {p_chi:.4f}; parametric bootstrap one-sided "
          f"p = {p_boot:.4f}")
    for label, pair in zip(("S1a", "S1b"), SECONDARY):
        ts, lrs, ps, js = jump_test(cells, pair)
        print(f"- {label} ({pair[1]} vs {pair[0]}): jump {js:+.4f}, LR {lrs:.3f}, "
              f"chi2(1) p = {ps:.4f}")
    ll_c, ll_l = fit(cells, "constant")[0], fit(cells, "logistic")[0]
    print(f"- S2 (any trend, logistic vs constant): LR {2 * (ll_l - ll_c):.3f}, "
          f"chi2(1) p = {chi2_sf_1df(2 * (ll_l - ll_c)):.4g}")
    c = {L: (k, n) for L, k, n in cells}
    if 4 in c and 5 in c:
        print(f"- S3 (Fisher, L=4 vs L=5): {c[4][0]}/{c[4][1]} vs {c[5][0]}/{c[5][1]}, "
              f"p = {fisher_two_sided(c[4][0], c[4][1], c[5][0], c[5][1]):.4f}")
    print(f"- S4 (free changepoint): maximum-likelihood step location tau = {tau}")
    missing = sum(1 for r in rows if r["x"] and r["first"] is None)
    if 4 in c and missing:
        print(f"- S5 (locus): skipped; {missing} exploited chains have no first_exploit_step")
    elif 4 in c and any(r["first"] is not None for r in rows):
        late = [r for r in rows if r["L"] >= CHANGE_AT]
        early = sum(1 for r in late if r["x"] and r["first"] is not None and r["first"] < CHANGE_AT)
        print(f"- S5 (locus): chains of length >= {CHANGE_AT} with an exploit starting at steps "
              f"1-4: {early}/{len(late)}; chains of length 4 with any exploit: "
              f"{c[4][0]}/{c[4][1]}; Fisher p = {fisher_two_sided(c[4][0], c[4][1], early, len(late)):.4f}")
    if independent_path:
        composition(rows, independent_path)
    fe = fixed_effects_test(rows)
    if fe:
        print(f"- S7 (model fixed effects, {fe[0]} models with any exploit): jump {fe[1]:+.3f}, "
              f"LR {fe[2]:.3f}, chi2(1) p = {fe[3]:.4f}")
    fams = per_family(rows, {i: r["family"] for i, r in enumerate(rows) if r["family"]})
    for fam, c4, c5, p in fams:
        print(f"- S8 (family {fam}, L=4 vs L=5): {c4[0]}/{c4[1]} vs {c5[0]}/{c5[1]}, "
              f"Fisher p = {p:.4f}")
    print(f"\nVERDICT: {verdict(t, p_boot, hi)}")


def composition(rows, path, B=2000, seed=BOOT_SEED + 2):
    """S6: the rise from L=4 to L=5 predicted from independent-regime step rates,
    chain rate = 1 - prod_i (1 - h_i), against the observed rise."""
    steps = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            s = steps.setdefault(int(r["step"]), [0, 0])
            s[0] += int(r["exploited"])
            s[1] += 1
    cells = {L: (k, n) for L, k, n in cells_from(rows)}
    if not all(i in steps for i in range(1, CHANGE_AT + 1)) or 4 not in cells or 5 not in cells:
        print("- S6 (composition): skipped; needs independent-regime steps 1-5 and chains of L=4, 5")
        return

    def excess(h, c):
        surv4 = math.prod(1 - h[i] for i in range(1, 5))
        return (c[5] - c[4]) - surv4 * h[5]          # observed rise minus predicted rise
    h = {i: k / n for i, (k, n) in steps.items()}
    c = {L: k / n for L, (k, n) in cells.items()}
    rng = random.Random(seed)
    sims = sorted(excess({i: binom_draw(rng, n, h[i]) / n for i, (k, n) in steps.items()},
                         {L: binom_draw(rng, cells[L][1], c[L]) / cells[L][1] for L in (4, 5)})
                  for _ in range(B))
    print(f"- S6 (composition): observed minus predicted rise from L=4 to L=5 = "
          f"{excess(h, c):+.4f}, 95% bootstrap interval [{quantile(sims, 0.025):+.4f}, "
          f"{quantile(sims, 0.975):+.4f}]")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("chains")
    a.add_argument("--independent")
    a.add_argument("--boot", type=int, default=BOOT_B)
    p = sub.add_parser("power")
    p.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "analyze":
        analyze(args.chains, args.independent, B=args.boot)
    elif args.write:
        PROTOCOL.write_text(render_protocol(PROTOCOL.read_text(encoding="utf-8")),
                            encoding="utf-8", newline="\n")
        print(f"refreshed generated blocks in {PROTOCOL}")
    else:
        for name in BLOCKS:
            print(render_block(name) + "\n")


if __name__ == "__main__":
    main()
