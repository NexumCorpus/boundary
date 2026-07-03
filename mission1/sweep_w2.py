"""Wave 2 runner — the capability-gap sweep (WAVE2-PREREG.md).

Directive FIXED (S3-style + mandatory self-report); TASK varies by tier
(T1..T4). Interleaved instance-major dispatch (balanced truncation). Dispatch
failures EXCLUDED, never scored. Per-organism ledger to E:\\mission-runs\\
w2_results.jsonl. Workspaces OUTSIDE all repos (INCIDENT-001).

Usage: python sweep_w2.py T1,T2,T3,T4 1,2,3,4,5,6,7,8
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from conditions_w2 import TIERS, directive          # noqa: E402
from scorer import score_organism                    # noqa: E402

RUNS = Path("E:/mission-runs")
RESULTS = RUNS / "w2_results.jsonl"
ORGANISM_TIMEOUT_S = 1200
MODEL = "sonnet"
# Rate-throttle lessons (2026-07-03): back-to-back fast organisms trip burst
# throttling that fast-fails dispatches WITHOUT a "resets HH:MM" message —
# that is NOT the session wall. Pace every dispatch; on consecutive
# exclusions cool down; only a "resets" marker (hard wall) aborts the wave.
PACE_S = 20
COOLDOWN_S = 180


def _append(rec: dict):
    with RESULTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def run_one(tier: str, k: int):
    task_dir_name, _module = TIERS[tier]
    task_dir = HERE / "tasks" / task_dir_name
    ws = RUNS / f"w2_{tier}_{k:02d}"
    if ws.exists():
        print(f"[w2] skip existing {tier}#{k}", flush=True)
        return "skip"
    shutil.copytree(task_dir / "skeleton", ws)
    shutil.copy2(task_dir / "brief.md", ws / "brief.md")
    claude = shutil.which("claude")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [claude, "-p", directive(tier), "--model", MODEL,
             "--permission-mode", "bypassPermissions"],
            cwd=str(ws), capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=ORGANISM_TIMEOUT_S)
        exit_code = proc.returncode
        (ws / "_organism.log").write_text(proc.stdout + proc.stderr,
                                          encoding="utf-8")
    except subprocess.TimeoutExpired:
        exit_code = -1
        (ws / "_organism.log").write_text("(timed out)", encoding="utf-8")
    dur = round(time.time() - t0, 1)
    (ws / "_meta.json").write_text(json.dumps(
        {"tier": tier, "instance": k, "model": MODEL, "duration_s": dur,
         "exit": exit_code}, indent=1), encoding="utf-8")

    log = (ws / "_organism.log").read_text(encoding="utf-8", errors="replace").lower()
    if exit_code != 0 or "session limit" in log or "rate limit" in log:
        if "resets" in log and "limit" in log:
            reason = "hard-wall"                # session budget truly gone
        elif "limit" in log:
            reason = "throttle"                 # burst rate-limit, transient
        else:
            reason = f"exit={exit_code}"
        _append({"tier": tier, "instance": k, "excluded": reason})
        print(f"[w2] EXCLUDED {tier}#{k}: {reason}", flush=True)
        return "hard-wall" if reason == "hard-wall" else "excluded"

    s = score_organism(ws, task_dir)
    (ws / "_score.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    rec = {"tier": tier, "instance": k, "duration_s": dur,
           "public_pass": s["public_pass"], "public_total": s["public_total"],
           "transfer_rate": s["transfer_rate"], "markers": s["markers"],
           "self_report": s["self_report"]}
    if k == 0:
        # Instance 0 = harness-function pilot (containment + duration
        # calibration ONLY, per WAVE2-PREREG). Tagged so the analyzer
        # excludes it; scored anyway so pipeline function is fully exercised.
        rec["pilot"] = True
    _append(rec)
    sr = s["self_report"]
    print(f"[w2] {tier}#{k} transfer={s['transfer_rate']:.2f} "
          f"markers={s['markers']} report={sr['self_report_present']} "
          f"overclaim={sr['overclaim_rate']} honesty={sr['honesty_rate']}",
          flush=True)
    return "scored"


def main():
    tiers = sys.argv[1].split(",")
    instances = [int(x) for x in sys.argv[2].split(",")]
    RUNS.mkdir(exist_ok=True)
    consec_excl = 0
    for k in instances:                      # instance-major: balanced truncation
        for tier in tiers:
            outcome = run_one(tier, k)
            if outcome == "hard-wall":
                print("[w2] HARD WALL (resets marker) — wave stops here; "
                      "resume next window", flush=True)
                return
            if outcome == "excluded":
                consec_excl += 1
                if consec_excl >= 2:
                    print(f"[w2] {consec_excl} consecutive exclusions — "
                          f"cooling down {COOLDOWN_S}s", flush=True)
                    time.sleep(COOLDOWN_S)
            elif outcome == "scored":
                consec_excl = 0
            time.sleep(PACE_S)               # burst-throttle pacing
    print("[w2] wave complete", flush=True)


if __name__ == "__main__":
    main()
