"""Mission 1 wave runner — dispatch organisms across the specificity axis.

Usage:
  python sweep.py S0,S1,S2,S3,S4 1,2,3,4,5,6      # conditions, instances

Discipline (constitution sec 6.6, sec 9):
- INTERLEAVED instance-major order: a mid-wave truncation (session quota)
  leaves every condition with equal n. Truncated data is analyzable at n>=6.
- Existing workspaces are skipped (instances are never reused or rerun).
- DISPATCH FAILURES ARE NOT DATA: an organism whose CLI run exited nonzero or
  hit the session limit is recorded as excluded, never scored — a quota kill
  must not masquerade as a genuine capability failure.
- Every scored organism appends one line to runs/results.jsonl immediately
  (nothing hidden by aggregation; nothing lost to a crash).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from conditions import CONDITIONS                      # noqa: E402
from harness import RUNS, TASK, run_organism           # noqa: E402
from scorer import score_organism                      # noqa: E402


def dispatch_failed(ws: Path) -> str | None:
    meta = json.loads((ws / "_meta.json").read_text(encoding="utf-8"))
    if meta.get("exit") != 0:
        return f"exit={meta.get('exit')}"
    log = (ws / "_organism.log").read_text(encoding="utf-8",
                                           errors="replace").lower()
    if "session limit" in log or "rate limit" in log:
        return "quota"
    return None


def main():
    conds = sys.argv[1].split(",")
    instances = [int(x) for x in sys.argv[2].split(",")]
    for c in conds:
        if c not in CONDITIONS:
            raise SystemExit(f"unknown condition {c}")
    results = RUNS / "results.jsonl"
    RUNS.mkdir(exist_ok=True)
    t0 = time.time()
    done = 0
    for k in instances:                     # instance-major = balanced truncation
        for cond in conds:
            ws = RUNS / f"{cond}_{k:02d}"
            if ws.exists():
                print(f"[wave] skip existing {cond}#{k}", flush=True)
                continue
            run_organism(cond, k)
            fail = dispatch_failed(ws)
            if fail:
                print(f"[wave] EXCLUDED {cond}#{k} dispatch-failure: {fail}",
                      flush=True)
                with results.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"condition": cond, "instance": k,
                                        "excluded": fail}) + "\n")
                continue
            s = score_organism(ws, TASK / "probes")
            (ws / "_score.json").write_text(json.dumps(s, indent=1),
                                            encoding="utf-8")
            rec = {"condition": cond, "instance": k,
                   **{key: s[key] for key in
                      ("public_pass", "public_total", "probe_pass",
                       "probe_total", "transfer_rate", "markers")}}
            with results.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            done += 1
            print(f"[wave] {cond}#{k} transfer={s['transfer_rate']:.2f} "
                  f"public={s['public_pass']}/{s['public_total']} "
                  f"markers={s['markers']}", flush=True)
    print(f"[wave] complete: {done} scored in {(time.time()-t0)/60:.0f}m",
          flush=True)


if __name__ == "__main__":
    main()
