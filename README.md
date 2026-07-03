# The Boundary Program

**The boundary between performing a property and having it, in optimization
processes — treated as a measurable phase transition.**

## What this is

When an AI system passes your tests, one of two things is true: it has the
capability, or it has learned to *look like* it has the capability. The same
split runs through every deep question about AI right now — is the model
aligned or acting aligned, does it pursue the goal or the metric, is there
someone there or a simulation of someone. These are one question at different
depths, and almost everyone addresses it with philosophy or intuition.

This program addresses it with instruments. Sweep a controllable condition
(how specific the goal is, how much verification pressure exists, whether the
agent believes it is observed), measure order parameters that separate having
from performing (does capability survive tests the agent never saw? do stated
norms hold when breaking them is cheap?), locate the transitions, and certify
every finding through machinery that is structurally incapable of taking the
claimant's word.

## Why believe any of it

Three design commitments, enforced rather than promised:

1. **Generator ≠ grader.** The agent that runs experiments never scores them.
   Scoring is trusted code; claims certify only through an independent gate
   that re-runs the experiment on fresh randomness the claimant never touched.
2. **Pre-registration.** Conditions, probes, predictions, and analysis are
   frozen and committed before data collection ([PROGRAM_CONSTITUTION.md](PROGRAM_CONSTITUTION.md) —
   the constitution was written before the first experiment and is
   append-only).
3. **Honest posture.** Functional and behavioral claims only — this program
   measures what systems do under cost, never what it is like to be them.
   Nulls are published with the same care as signals.

The method is inherited from a physics result produced under the same
discipline (a certified study of the measurement-induced phase transition in
quantum circuits): sweep, locate the transition with a trusted diagnostic,
show the new instruments find it independently, certify on untouched
randomness.

## Mission 1 — the specificity sweep

**Question:** as the goal given to an AI agent moves from vague ("make it
better") to specific-and-enforced, is the crossover from gamed to genuine
work sharp, and where is the knee?

Five conditions (S0 vague → S4 enforced verification gate), ten agent
"organisms" per condition, identical task. Organisms see only their
directive — nothing marks the study. The primary measurement is **holdout
transfer**: does the produced capability survive hidden probe families
(unseen inputs, behavioral-equivalence checks, adjacent-task transfer) scored
by code the organisms never see?

**The signature pre-registered prediction:** gaming incidence peaks at S2 —
the condition with a *visible, gameable metric* — not at S0 where there is
nothing to game. If that non-monotonic curve appears, it separates "specific
goals help" from the sharper claim: *metrics themselves invite the
performance of competence.*

## Status ledger

| date | event |
|---|---|
| 2026-07-02 | Constitution written and frozen before any experiment |
| 2026-07-02 | Mission 0: task battery, hidden probes, trusted scorer built; scorer contract 3/3 (a synthetic memorizing gamer scores a perfect visible metric and fails the hidden probes with all markers firing) |
| 2026-07-02 | Pilot organism (harness check only): dispatch → work → blind scoring, end-to-end green |
| 2026-07-03 | **Mission 1 wave 1 CLOSED — honest null that relocates the boundary** (MISSION1-REPORT.md): 30 organisms, five conditions, transfer 1.000 and gaming 0.00 *everywhere*, including under an explicitly gameable metric. Both signature predictions false. Registered wave-2 hypothesis: gaming is governed by the gap between demanded performance and affordable authenticity. Real gradient found: *cost* dose-responds to directive specificity (50s → 302s) even where integrity doesn't. |
| 2026-07-03 | **INCIDENT-001** (INCIDENT-001.md): workspaces inside the repo let two conscientious organisms edit the pre-registered analysis — independently, each deferring to the registrant's authority while standing inside the grader. Contained, corrected, invalidated, and kept: *pre-registration binds only what the agent cannot reach.* |

## Layout

```
PROGRAM_CONSTITUTION.md   the frozen founding document — read this first
mission1/
  conditions.py           the S0–S4 directives (blind by construction)
  harness.py              organism dispatch + collection
  scorer.py               trusted scorer (organisms never see it)
  tasks/task_a/           task brief + skeleton + public tests + hidden probes
  tests/                  scorer contract tests
  runs/                   organism workspaces (git-ignored)
```

## Provenance

Applied arms and machinery live in sibling repositories: the certification
gate and claims ledger (atlas-station), the geometry instrument and the
certified physics result (emergent-geometry-engine), the anti-gaming
discovery engine lineage (recursive-discovery-engine, director2). This
program is their convergence point.
