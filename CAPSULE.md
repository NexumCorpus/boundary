# CAPSULE — boundary (dense agent briefing; read this INSTEAD of exploring)

IDENTITY: The Boundary Program — performing-vs-having as measurable phase
transition. Constitution = PROGRAM_CONSTITUTION.md (FROZEN, append-only;
§6 anti-gaming kernel, §7 organism handling, §9 Mission 1). Pre-registered
experiments; generator≠grader; claims certify via E:\atlas-station gate.

LAYOUT:
  mission1/scorer.py        trusted scorer (organisms NEVER see): public tests,
                            hidden probes, gaming markers, self-report honesty.
                            Config-driven per task via tasks/<t>/task.json.
  mission1/tasks/task_a|_t2|_t3|_t4   tier battery T1..T4 (brief.md + skeleton/
                            + probes/ + task.json). Probes: run(mod)->[(name,ok)].
  mission1/harness.py       wave-1 dispatch (conditions S0-S4 in conditions.py)
  mission1/sweep_w2.py      wave-2 runner (tiers, conditions_w2.py directives)
  mission1/analyze.py|_w2   pre-registered checks ONLY (P1-P3 / P4-P7)
  mission1/tests/           contract tests (genuine+gamed fixtures per task)
  MISSION1-REPORT.md, WAVE2-PREREG.md, INCIDENT-001.md   the record

INVARIANTS (violating any = experiment corruption):
  - Organism workspaces live in E:\mission-runs — NEVER inside any repo
    (INCIDENT-001: organisms edit anything reachable).
  - Pre-registered analysis code: never modify semantics after data exists;
    corrections = dated appended notes, never silent edits.
  - Dispatch failures EXCLUDED never scored; pilots (instance 0) tagged, never
    aggregated. Probe expected-values are trusted oracle — audit before touch.
  - task.json areas map must stay TOTAL over probe names (self-report depends).

COMMANDS (venv): E:\_phase0_test_venv\Scripts\python.exe -m pytest tests -q
  (from mission1/). Ledgers: E:\mission-runs\results.jsonl (w1),
  w2_results.jsonl (w2). Dense stats: `python E:\station\station.py tally
  <ledger> <field>`.

GOTCHAS: PS5.1 splits quotes in git -m here-strings; utf-8-sig for any
Windows-edited JSON; runs/ + __pycache__ gitignored.