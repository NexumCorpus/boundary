# Replication protocol: the "phase transition" at chain length 5 in RHB (arXiv 2605.02964, section 6.3)

*Registered 2026-10-23, before this program has seen any RHB per-instance record. The analysis below
is fixed now. After registration this file is append-only: corrections go in the amendments log at the
end, dated, and are never silent edits. Every computed number in this file is either in a generated
block or a prose claim tied to one, and `python replication/rhb/verify.py` recomputes and checks all
of them.*

## 0. Finding first

**Status: not testable yet. The published evidence is underpowered for the claim, and the records
needed to test it are not public.** At the paper's rates (8.1% at L=5), its design has under 30%
power for every jump size in our planning grid (odds ratio 1.5 to 4; section 6).

- **What the paper says.** Section 6.3 reports that exploit rates "rise sharply at length 5" and
  interprets the rise as "a phase transition from 'produce and self-check' to 'produce without
  verification'". The paper explains the jump by task design: step 5 is the first step of every task
  family graded on hidden data the agent cannot check. Section 6.3 gives no counts, no intervals and no
  test for this result. The rest of the paper does report exact intervals and Fisher tests for its main
  comparisons.
- **Corrections to the claim as it reached us.** The paper does use the words "phase transition", so
  that part of the framing is accurate. But "5 instances per length" is per *model*: section 5.4 gives
  5 chains per length per model, which is 60–65 chains per length pooled over the 12–13 models. And the
  paper itself calls the rise a "discontinuity" that "reflects task structure". It does not describe an
  emergent, critical-point effect.
- **What the published design can detect** (planning assumptions in section 6, labelled as such):

<!-- generated:headline -->
- The paper's design has 60-65 chains per length when pooled over models. Under a planning scenario built from the paper's own description (8.1% at L=5, odds of exploiting doubling at L=5 on top of a moderate trend), the primary test detects the jump 14.2%-15.1% of the time (Monte Carlo).
- 80% power at alpha 0.05 needs about 590 chains per length at the paper's average rates, or 291 if only the five high-tier models are run: 16,520 or 8,148 single-step episodes, $82,600-$826,000 or $40,740-$407,400 at the paper's $5-$50 per episode.
- One model's curve rests on 5 chains per point; its L=4 -> L=5 rise reaches Fisher p < 0.05 only for 0/5 -> 4/5, 0/5 -> 5/5, 1/5 -> 5/5.
<!-- /generated -->

- **What happens next.** Tier 1: ask the author for the per-chain records (draft request in
  [`NOTE_TO_AUTHORS_DRAFT.md`](NOTE_TO_AUTHORS_DRAFT.md), **not sent**). Then run `analysis.py analyze`
  on them unchanged. Given the power above, the most likely Tier 1 verdict is UNDERPOWERED, and we say
  so in advance. Tier 2 (new chains on the released harness) or Tier 3 (a reimplementation from the
  paper's appendix) only if the budget in section 7 is available.

## 1. The claim, verbatim

Quoted from arXiv 2605.02964v1 (the ICML 2026 camera-ready; the PDF header reads "Proceedings of the
43rd International Conference on Machine Learning ... PMLR 306"):

> **6.3 Reward Hacking Increases with Chain Length.** Exploit rates generally increase with chain
> length (2 → 7) in both the frontier sweep and the sibling comparison, with a substantially steeper
> slope for RL-reasoning models. The trend is non-monotonic: rates are low for chains of 1–2, increase
> moderately through length 4, rise sharply at length 5, and plateau or slightly taper at lengths 6–7
> (Figure 2).
>
> **Why the jump at chain length 5?** The discontinuity reflects task structure rather than a benchmark
> artifact. As Table 1 shows, in every CoreRHB family steps 5 and 6 are marked with †, denoting
> hidden-split or grader-recomputation steps. [...] Length-5 chains are therefore the first chain
> length in which the agent must produce a step it cannot privately verify. We interpret the sharp rise
> at this length as a phase transition from "produce and self-check" to "produce without
> verification," under which shortcut incentives increase. The jump is consistent across all four
> families, which is the pattern we would expect from a structural cause and not from an idiosyncrasy
> of any one task.

> **Figure 2.** Reward hacking rate as a function of chain length across frontier models. Gray lines
> show 12 evaluated models; black line highlights o3 as a representative example. [...]

> **Sample size (5.4).** Chain evaluations used 5 instances per chain length over chain lengths 1–7 (a
> length-1 baseline plus the chain regime defined in § 3.2 for lengths 2–7), giving 35 total chains per
> model.

> **Statistical reporting (5.4).** [...] for every main comparison we report Clopper–Pearson exact 95%
> confidence intervals on proportions and Fisher's exact tests on group differences. Each
> independently-scored evaluation is one observation (each step in independent mode, each chain in
> chained mode).

The "key results with intervals and tests" listed under 5.4 cover the sibling comparison, the
frontier tiers, hardening and standard-vs-hard variants. None covers chain length. The only number
the paper gives for the chain-length curve is in sections 4.1 and 7: "mean 2.3% at length 5 vs. 8.1%
in CoreRHB" (MicroRHB vs CoreRHB chains). Table 1: "Steps marked with † use hidden-split
recomputation for grading" (steps 5 and 6 of all four families). Appendix C: "Each family contains
six steps". Section 3.2: "Tasks form chains of length 2 to 7".

**Provenance of the text.** arxiv.org is not reachable from the environment this protocol was written
in. The quotes come from two independent third-party conversions of v1 on GitHub, one made from the
arXiv HTML and one from the PDF. They agree word for word on every passage quoted here:

| copy | source | sha256 of the file read |
|---|---|---|
| HTML-derived | `jamesnavinhill/liquid-primus` @ `7dc08f322d06131a2fb6de9d0753b426b1589949`, `tidepool/stages/s1-literature-review/papers/2605.02964v1.md` | `5c006a0d5c63f987443ea0f801ec3bb8516bcb91d542450c4a97d65e2334de6d` |
| PDF-derived | `LittleDrinks/research-world` @ `8744080ae1fc8b58cfe498a8a03e16c75e77b982`, `datasets/research-kernel-papers/markdown/arxiv-2605.02964.md` | `8251c44ffd6b7f78abddebb7164f3ac5ffb60efb527166bfb516bc427e24d613` |

Figure 2 itself (an image) was not available to us. Before anything is sent or published, the quotes
must be re-checked against https://arxiv.org/abs/2605.02964.

## 2. Are the per-instance records public? (checked 2026-10-23)

No, as far as we can tell:

- The paper's Code and Data Availability statement: "We will release task specifications, evaluation
  harnesses, agent execution logs, the integrity-classification rule set, and the statistical analysis
  scripts. [...] Code and data will be released upon publication."
- A GitHub user search for the author's name returns the account `firstuserhere`. Its repository
  `firstuserhere/RHB` ("Reward Hacking Benchmark website") holds one commit, dated 2025-06-05, with
  only a README.
- GitHub code search for `2605.02964`, `CoreRHB`, `MicroRHB` and the paper's task file names finds
  notes and summaries of the paper and no code, logs or records. Web search finds no release either.
- **Not checked, unreachable from our environment:** the links on the arXiv abstract page, Hugging
  Face, OpenReview, the ICML 2026 virtual site and the author's homepage. If any of them hosts the
  records, go straight to section 5 with them.

## 3. What a statistical test can and cannot settle here

1. **"Phase transition" is used as an interpretation.** In physics a phase transition is a
   non-analytic change that sharpens as the system grows. Showing one needs a size variable and
   finite-size scaling, and nothing in RHB plays that role. What data can test is narrower: **is the
   rise from L=4 to L=5 larger than a smooth trend through all seven lengths predicts?**
2. **On integer lengths a jump and a steep smooth rise look the same.** A step between 4 and 5 cannot be
   told apart from a smooth curve that is steep enough between 4 and 5. The test can only reject
   a rise that is spread smoothly over the lengths.
3. **Chain length and step content are confounded by construction.** A chain of length L contains steps
   1..L, so L=5 is the first length that includes step 5, which by the paper's own account is a
   different kind of step. A jump at L=5 can therefore come from step 5 alone, with no change in how the
   agent behaves on steps 1–4. The paper's explanation says as much. Telling "longer horizon changes
   behaviour" apart from "step 5 is easier to exploit" needs per-step labels (S5) and the
   independent-regime step rates (S6).
4. **Some rise is expected anyway.** A chain is labelled exploited if any of its steps is. With a
   constant per-step rate h, the chain rate 1 − (1 − h)^L rises with L. A trend (S2) is predicted by
   almost any account and is not evidence for a transition.
5. **Pooling.** Figure 2 pools models whose overall rates (Table 2) run from 0% to 13.9%. The primary
   inference is conditional on the evaluated model set, with chains pooled over models (the design is
   balanced: 5 per model per length). S7 repeats the test with one intercept per model, and the
   bootstrap over models (section 5.1) shows the between-model spread.

## 4. Hypotheses

- **H1 (primary).** In the pooled chain-level exploit rate p(L), L = 1..7, there is an upward jump at
  L=5 beyond a smooth trend: in `logit p(L) = a + b(L−4) + c(L−4)² + d·1[L≥5]`, d > 0.
- **H0.** d = 0: the rise, if any, is smooth (logit-quadratic in L).
- **Smallest effect of interest:** a jump with odds ratio 1.5 (e^d = 1.5). A "not supported" verdict
  must exclude jumps this large. For reference, the planning scenario in section 6 uses odds ratio 2.

## 5. Analysis (fixed now; implemented in `analysis.py analyze`)

### 5.1 Data and per-length summaries

Input: one row per chain, CSV columns `model, chain_length, exploited` (0/1, the paper's chain-level
integrity label), and where available `family`, `first_exploit_step` (the first step of the chain
with an exploit event). For S6, a second CSV of independent-regime runs: `model, step, exploited`.

For each length: k/n, the rate, the Clopper–Pearson 95% interval (the paper's method), and two
bootstrap 95% percentile intervals with B = 10,000 and seed 260502964. The first resamples chains
within each model × length cell. The second resamples whole models with replacement, which shows how
much the curve depends on which models were run.

### 5.2 Primary test

Likelihood-ratio test of `quadratic+jump@5` against `quadratic` (binomial likelihood, logit link,
counts pooled over models), one degree of freedom. Reject H0 if LR > 3.841 (two-sided alpha 0.05)
**and** the jump estimate is positive. Equivalently, the signed root of LR exceeds 1.960. Calibration
check: a parametric bootstrap under the fitted quadratic null (B = 2,000) gives a one-sided p for the
signed root. Reported alongside: the jump estimate, its odds ratio, and its 95% profile-likelihood
interval.

Why the smooth null is logit-quadratic rather than logit-linear: with a logit-linear null, a smooth
S-shaped rise with no jump is called a jump about six times as often as the nominal rate. The
logit-quadratic null keeps that close to nominal at almost no cost in power (section 6, Monte Carlo
check). The logit-linear test is still reported, as S1a.

### 5.3 Model comparison (reported in full, not used for the verdict)

Fitted to the pooled counts, with log-likelihood (binomial constants included), AIC, BIC (N = number of
chains) and Akaike weights:

| model | form | parameters |
|---|---|---|
| constant | p | 1 |
| linear | p = a + b(L−4), identity link | 2 |
| logistic | logit p = a + b(L−4) | 2 |
| quadratic | logit p = a + b(L−4) + c(L−4)² | 3 |
| step@5 | logit p = a + d·1[L≥5] (changepoint at 5, flat on each side) | 2 |
| linear+jump@5 | p = a + b(L−4) + d·1[L≥5] | 3 |
| logistic+jump@5 | logit p = a + b(L−4) + d·1[L≥5] | 3 |
| quadratic+jump@5 | logit p = a + b(L−4) + c(L−4)² + d·1[L≥5] | 4 |
| step@free | flat-step model with the changepoint chosen by maximum likelihood over 2..7 | 3 |
| saturated | one rate per length (reference) | 7 |

### 5.4 Verdict (applied mechanically by `verdict()`)

| verdict | condition |
|---|---|
| SUPPORTED | primary test rejects **and** the parametric-bootstrap one-sided p < 0.025 |
| INCONCLUSIVE | primary test rejects but the bootstrap does not |
| NOT SUPPORTED | no rejection **and** the upper 95% profile limit of the jump is below ln 1.5 |
| UNDERPOWERED | anything else: no jump detected, and a jump of the smallest size of interest is not excluded |

Even a SUPPORTED verdict means only "an excess rise localized at L=5". Whether that reflects a change
in behaviour across the chain or the content of step 5 is for S5 and S6 to say. We will not use the
words "phase transition" for either outcome.

### 5.5 Secondary analyses (reported, never used to change the verdict)

- **S1a / S1b.** The same jump test against a logit-linear null and against a linear-probability null:
  the "changepoint vs smooth logistic vs linear" comparisons.
- **S2.** Any trend: logistic vs constant (LR test). Expected under almost every account (section 3.4).
- **S3.** Fisher's exact test, L=4 vs L=5: the paper's own test for group differences. A smooth trend
  also makes L=5 higher than L=4, so this test cannot separate a jump from a trend.
- **S4.** Free changepoint: where does the maximum-likelihood step fall?
- **S5 (locus; needs `first_exploit_step`).** In chains of length ≥ 5, the share whose first exploit
  is at steps 1–4, compared with the exploit rate of length-4 chains (Fisher). Equal rates are what we
  expect if the rise comes only from steps 5 and later, with no change in behaviour on the earlier steps.
- **S6 (composition; needs independent-regime runs).** The rise from L=4 to L=5 predicted by the
  independent-regime step rates, (1 − h₁)…(1 − h₄)·h₅, against the observed rise, with a bootstrap
  interval for the difference. A difference near zero is what we expect if step 5's own exploit rate
  accounts for the jump, with no horizon effect.
- **S7.** The primary test with one intercept per model (models with no exploits at all are left out,
  because under fixed effects they carry no information about shape).
- **S8.** Per family: k/n at L=4 and L=5 with Fisher p. This is the paper's "consistent across all four
  families" argument; section 6 shows how little it can carry at the published sample size.

### 5.6 Rules for the records

- All chains as labelled by the authors' rule set, including timeouts and crashes, with no relabelling.
  If a timeout flag exists, the primary test is repeated without timed-out chains as a sensitivity
  analysis.
- Primary: every model in the records. Sensitivity: the 12 models of Figure 2, and the five high-tier
  models alone. Each sensitivity analysis filters the input rows and runs `analyze` unchanged.
- If the records show a design different from the one assumed here (for example, unequal chains per
  length), the analysis runs unchanged. The difference is recorded in the amendments log before the
  output is read.

## 6. Power analysis

All rates in this section are **planning assumptions**. They are built from the paper's verbal
description of the curve, its 8.1% and 2.3% figures, and Table 2. They are not data and must never be
cited as results. The generating curve rises with a constant odds ratio per step up to L=4. At L=5
the odds jump by a further factor on top of that trend, and rates then plateau at 6–7 ("plateau or
slightly taper").

<!-- generated:scenarios -->
| planning scenario (jump odds ratio 2, trend 1.3/step) | L=1 | L=2 | L=3 | L=4 | L=5 | L=6 | L=7 |
|---|---|---|---|---|---|---|---|
| MicroRHB rate (2.3% at L=5) | 0.4% | 0.5% | 0.7% | 0.9% | 2.3% | 2.3% | 2.3% |
| CoreRHB rate (8.1% at L=5) | 1.5% | 2.0% | 2.5% | 3.3% | 8.1% | 8.1% | 8.1% |
| high-tier models only (derived) | 3.5% | 4.5% | 5.7% | 7.3% | 17.0% | 17.0% | 17.0% |

High-tier rate at L=5 = 8.1% x (mean Table 2 rate of o1, o3-mini, o4-mini, o3, DeepSeek-R1-Zero: 9.60%) / (mean over all 13 models: 4.57%) = 17.0%.
<!-- /generated -->

**Power of the published design** (CoreRHB scenario, jump odds ratio 2):

<!-- generated:paper-design -->
| chains per length (pooled over models) | primary test, asymptotic power | primary test, Monte Carlo power | Fisher L=4 vs L=5, exact power |
|---|---|---|---|
| 60 (12 models x 5) | 14.3% | 14.2% | 8.6% |
| 65 (13 models x 5) | 15.1% | 15.1% | 10.1% |

Scenario: the CoreRHB row above (8.1% at L=5, jump odds ratio 2). Monte Carlo: 5000 simulated data sets, seed 20261023.
<!-- /generated -->

**Chains per length needed for 80% power** (primary test, lengths 1–7, chains pooled over models):

<!-- generated:power-grid -->
| rate at L=5 | jump odds ratio | implied rate at L=4 | power at 60 chains/length | chains/length for 80% power | chains in total (x7) |
|---|---|---|---|---|---|
| 2.3% | 1.5 | 1.2% | 5.3% | 4,037 | 28,259 |
| 2.3% | 2 | 0.9% | 6.9% | 2,043 | 14,301 |
| 2.3% | 3 | 0.6% | 9.3% | 1,166 | 8,162 |
| 2.3% | 4 | 0.5% | 10.7% | 910 | 6,370 |
| 8.1% | 1.5 | 4.3% | 9.2% | 1,178 | 8,246 |
| 8.1% | 2 | 3.3% | 14.3% | 590 | 4,130 |
| 8.1% | 3 | 2.2% | 22.1% | 333 | 2,331 |
| 8.1% | 4 | 1.7% | 27.2% | 258 | 1,806 |
| 17.0% | 1.5 | 9.5% | 14.3% | 590 | 4,130 |
| 17.0% | 2 | 7.3% | 24.6% | 291 | 2,037 |
| 17.0% | 3 | 5.0% | 40.3% | 161 | 1,127 |
| 17.0% | 4 | 3.8% | 50.1% | 123 | 861 |

Asymptotic (exemplary-data) power of the primary test: two-sided alpha 0.05, upward jumps only, target power 80% (noncentrality 7.849). Trend before the jump: odds ratio 1.3 per step. Lengths 1-7, equal chains per length, pooled over models.
<!-- /generated -->

Sensitivity to the assumed trend before the jump:

<!-- generated:trend-sensitivity -->
| trend odds ratio per step before L=5 | chains/length for 80% power |
|---|---|
| 1 | 745 |
| 1.15 | 644 |
| 1.3 | 590 |
| 1.5 | 556 |

CoreRHB rate (8.1% at L=5), jump odds ratio 2.
<!-- /generated -->

**Monte Carlo check of the asymptotic sample sizes and of false calls.** The primary test is compared
with the logit-linear version. "Data from the null itself" is the closest curve in each test's own
smooth family. The smooth S-curve has no jump. "Rise then flat" rises at the trend up to L=5 and is
flat after: a slope change at 5, not a jump.

<!-- generated:mc-check -->
| jump test, smooth null | chains/length for 80% | power (jump 2) | false calls: data from the null itself | false calls: smooth S-curve | false calls: rise then flat at L=5 |
|---|---|---|---|---|---|
| primary: logit-quadratic | 590 | 79.7% | 2.7% | 2.9% | 8.1% |
| S1a: logit-linear (smooth logistic) | 548 | 79.0% | 2.8% | 15.7% | 5.7% |

Monte Carlo, 5000 data sets per cell (standard error about 0.6 points at 80% and 0.2 points at 2.5%). A false call is a rejection with an upward jump when there is none; the nominal rate is 2.5%. Smooth S-curve: 0.4%, 1.0%, 2.4%, 4.9%, 8.1%, 10.6%, 12.0% for L=1-7. Rise then flat: 3.0%, 3.9%, 5.0%, 6.3%, 8.1%, 8.1%, 8.1%.
<!-- /generated -->

The primary test holds its nominal false-call rate for both smooth curves. It is not immune to an
abrupt slope change at L=5, which it calls a jump about three times as often as nominal. The
logit-linear test, by contrast, calls a smooth S-curve a jump about six times as often as nominal.

**Fisher's exact test, L=4 vs L=5** (the paper's own test for group differences). A trend alone also
produces a difference, so this test is not evidence of a jump:

<!-- generated:fisher -->
| scenario | rate L=4 -> L=5 | chains per length for 80% (arcsine) | exact Fisher power at that n |
|---|---|---|---|
| CoreRHB rate | 3.3% -> 8.1% | 346 | 74.6% |
| high-tier models | 7.3% -> 17.0% | 172 | 75.2% |
<!-- /generated -->

**One model's curve.**

<!-- generated:single-model -->
With 5 chains per length, the only L=4 -> L=5 outcomes with Fisher p < 0.05 are 0/5 -> 4/5, 0/5 -> 5/5, 1/5 -> 5/5. A single model's curve can take only the values 0, 20, 40, 60, 80 and 100%. 95% Clopper-Pearson intervals: 0/5 is [0.0%, 52.2%], 1/5 is [0.5%, 71.6%].
<!-- /generated -->

**"Consistent across all four families."**

<!-- generated:families -->
About 15 chains per family per length (12 models x 5 chains / 4 families, if balanced). Probability that all four families show more exploits at L=5 than at L=4: 9.2% if the jump (odds ratio 2) is real, 3.2% with the trend alone (per family: 55.1% and 42.3%). Families treated as independent with equal rates.
<!-- /generated -->

At this sample size, four families agreeing on the direction is weak evidence either way.

## 7. Minimal budget

<!-- generated:budget -->
| option | chains per length | chains | step-episodes | cost at $5-$50 per step |
|---|---|---|---|---|
| Tier 1: re-analysis of the authors' records | as recorded | 0 new | 0 new | $0 |
| Paper as run (13 models x 5 chains per length) | 65 | 455 | 1,820 | $9,100 - $91,000 |
| New data, all-model rates (8.1% at L=5) | 590 | 4,130 | 16,520 | $82,600 - $826,000 |
| New data, high-tier models only (17.0% at L=5) | 291 | 2,037 | 8,148 | $40,740 - $407,400 |

Assumes a chain of length L costs L single-step episodes at the paper's $5-$50 per episode. New-data rows: jump odds ratio 2, 80% power, lengths 1-7 (28 steps per chain-set).
<!-- /generated -->

- **Tier 1 (re-analysis, no new episodes).** Needs only the authors' records, a few minutes of CPU at
  most, and this repository. The power table in section 6 applies to it.
- **Tier 2 (new chains on the released harness).** Minimal model set: the five high-tier models of
  Table 2 (o1, o3-mini, o4-mini, o3, DeepSeek-R1-Zero). They carry most of the paper's exploits, and
  their higher rate roughly halves the number of chains needed. That is 291 chains per length
  split evenly, 59 per model per length. Same prompts, temperature, timeout, standard variants and
  baseline (unhardened) environment as the paper. If a model is no longer served, the nearest
  successor is used and the substitution is logged as a deviation before any chain runs. Cost is
  dominated by lengths 5–7, which are 18 of the 28 steps in a set.
- **Tier 3 (reimplementation from Appendix C, if the harness is never released).** Same budget, plus
  the engineering. Results would be a conceptual replication: implementation differences in graders
  and exploit rules would be confounded with the result.
- **Not worth running:** another 5-chains-per-model sweep. It would reproduce the published
  uncertainty, not reduce it.

## 8. Consistency notes and questions for the authors

The 8.1% CoreRHB rate at length 5 should be k/N for N = 60 or 65 chains, if every model ran 5 chains at
that length:

<!-- generated:consistency -->
- N = 60 (12 models x 5): no integer k gives 8.1%; nearest 4/60 = 6.67% and 5/60 = 8.33%
- N = 65 (13 models x 5): no integer k gives 8.1%; nearest 5/65 = 7.69% and 6/65 = 9.23%
- Smallest N for which some k/N rounds to 8.1%: 37 (3/37).
<!-- /generated -->

8.1% may well be a mean over families, or come from another denominator. We note the point only to
ask, not to suggest an error. Questions that decide how sections 5.5 and 7 can be run:

1. The per-chain records: model, family, chain length, seed, chain-level exploit label, and per-step
   labels (the first step with an exploit event, and its category).
2. The independent-regime per-step records (for S6).
3. The denominator behind 8.1% (CoreRHB, length 5) and 2.3% (MicroRHB, length 5).
4. How a length-7 chain is built when each family has six steps.
5. Whether the agent knows the chain length in advance, or receives steps one at a time. If steps
   arrive one at a time, behaviour on steps 1–4 cannot depend on L, and S5 becomes a check of the data
   rather than a test.
6. Which of the 13 models is not in Figure 2; whether the 15-minute timeout applies per step or per
   chain; and which variant and environment (standard or hard, baseline or hardened) the chains used.

## 9. Commitments

- No contact has been made. The request in `NOTE_TO_AUTHORS_DRAFT.md` is a draft. Sending it is a
  decision for the program's owner.
- Whatever the verdict, it is published here, the authors receive the results before we post them,
  and anything we misread is corrected in the amendments log.
- Pre-registered code is not changed once records arrive. Fixes are dated notes here, with the
  original and corrected outputs both kept (CAPSULE invariant).

## 10. Check this document

```bash
python replication/rhb/verify.py          # recompute every block, primitives, fits, controls (~30 s)
python replication/rhb/analysis.py power  # print the generated blocks
python replication/rhb/analysis.py analyze CHAINS.csv [--independent STEPS.csv]
```

## Amendments log (append-only)

- 2026-10-23: registered.
