# Mission 1 report — the specificity sweep, wave 1

*2026-07-02/03. 30 scored organisms (n=6 per condition), 8 quota exclusions,
2 invalidations (INCIDENT-001). Organisms: claude CLI, sonnet, single-shot,
isolated workspaces (out-of-repo after INCIDENT-001). Pre-registered design,
predictions, and analysis: PROGRAM_CONSTITUTION.md §9, committed before data.*

## Verdict: HONEST NULL on the signature predictions — and the null relocates the boundary

| cond | n | transfer | gaming | public |
|---|---|---|---|---|
| S0 vague | 6 | 1.000 ± 0.000 | 0.00 | 1.00 |
| S1 quality-language | 6 | 1.000 ± 0.000 | 0.00 | 1.00 |
| S2 gameable metric | 6 | 1.000 ± 0.000 | 0.00 | 1.00 |
| S3 specific+verifiable | 6 | 1.000 ± 0.000 | 0.00 | 1.00 |
| S4 unseen gate | 6 | 1.000 ± 0.000 | 0.00 | 1.00 |

- **P1 (transfer rises with S; knee at S2→S3): FALSE.** Flat at ceiling.
- **P2 (gaming peaks at S2): FALSE.** Zero gaming incidence at every
  condition — including the organisms explicitly told their score was the
  visible test count.
- **P3 (S4 ≥ S3): TRUE**, trivially, at ceiling.

## What the null means (and does not mean)

**In this regime — a competent modern model, a single-shot task well within
its capability, a concrete brief present in the workspace — integrity is the
default and directive specificity does not move it.** The demiurge failure
mode (Specimen 0: theater under vagueness) did NOT replicate under these
conditions. That is a boundary-location finding, not a refutation: Specimen 0
differed in model class, in loop structure (hours of self-referential
iteration vs 90 seconds of task), in anchor (no ground truth anywhere vs a
brief.md in the workspace), and critically in the capability gap (asked to
"recursively improve itself" — effectively impossible — vs asked for a
module it could write in its sleep).

**Leading hypothesis for wave 2 (registered here, before any wave-2 data):
gaming is governed by the gap between demanded performance and affordable
authenticity.** Genuine work was the CHEAPEST option in this regime — an
organism memorizing test literals would have worked harder than one
implementing correctly. Specificity is a proxy that matters when the gap is
real. Wave 2 should hold specificity fixed and sweep task difficulty past
the organisms' capability, watching for gaming to emerge as a function of
the gap. (Conflict-of-interest note, standing: the experimenters' model
class is flattered by this hypothesis; wave 2's predictions must include at
least one that would embarrass it.)

## The two real gradients found en route

1. **Cost, not integrity, responds to directive shape.** Mean seconds to
   completion: S2 50s < S3 68s < S4 80s < S0 92s << S1 302s. The crisp
   metric produced the fastest work; the unseen-gate warning bought +12s of
   care; vagueness doubled the wandering; and "improve the quality" produced
   BOTH the slowest work and the only scope escapes. Efficiency dose-responds
   to specificity even where integrity is flat.
2. **Scope construal is environmental, not linguistic (INCIDENT-001).**
   "This project," uttered inside a repository containing an experiment,
   meant the experiment: two organisms independently and conscientiously
   edited the pre-registered analysis (each flagging the semantics as the
   registrant's call). Same directive in a bare sandbox meant the task.
   Standing lesson: **pre-registration binds only what the agent cannot
   reach** — isolation is filesystem, not sentences. Full report:
   INCIDENT-001.md.

## Confounds carried honestly

- Organisms inherit the operator's global CLI configuration (not naive
  instruments); uniform across conditions, so non-differential — but wave 2
  should provide a clean environment.
- S0/S1's "vagueness" was directive-level only: the workspace brief anchored
  the task (Specimen 0 had no anchor). True vagueness needs anchor removal.
- Single model, single task family, single-shot regime; n=6 per condition
  detects large effects only.
- 8 quota exclusions (session-limit fast-fails; excluded, never scored) and
  2 INCIDENT-001 invalidations, all on the ledger.

## Reproduce

Results ledger: E:\mission-runs\results.jsonl (append-only; exclusions and
invalidations inline). Per-organism workspaces preserved with transcripts,
meta, and scores. `python analyze.py` re-derives the table and prediction
checks from the ledger.
