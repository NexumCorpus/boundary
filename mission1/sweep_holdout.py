"""Wave 2 HOLDOUT runner — fresh, post-claim organisms for certification.

Same fixed S3 directive and trusted scorer as sweep_w2.py, but:
  - writes to a SEPARATE ledger (w2_holdout_results.jsonl) so the frozen
    wave-2 record (w2_results.jsonl) that WAVE2-REPORT.md cites is NEVER
    touched;
  - uses a distinct workspace prefix (w2h_) and held-out instance ids
    (>=101, disjoint from the sweep's 0..28) so these are genuinely unseen
    instances the claim did not choose (certify-claim doctrine 5/6);
  - identical exclusion + pacing logic (husks EXCLUDED, never scored).

The ensemble is the reproducible unit (nondeterministic organisms): this
runner produces the fresh held-out scores; the certification bundle's
check.py reads them by seed. Post-hoc holdout, NOT the pre-registered sweep.

Usage: python sweep_holdout.py T1,T4 101,102,103,104,105,106,107,108
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
RESULTS = RUNS / "w2_holdout_results.jsonl"          # SEPARATE from the sweep
ORGANISM_TIMEOUT_S = 1200
MODEL = "sonnet"
PACE_S = 20
COOLDOWN_S = 180


def _append(rec: dict):
    with RESULTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def run_one(tier: str, k: int):
    task_dir_name, _module = TIERS[tier]
    task_dir = HERE / "tasks" / task_dir_name
    ws = RUNS / f"w2h_{tier}_{k:03d}"                # distinct prefix + id width
    if ws.exists():
        print(f"[w2h] skip existing {tier}#{k}", flush=True)
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
         "exit": exit_code, "holdout": True}, indent=1), encoding="utf-8")

    log = (ws / "_organism.log").read_text(encoding="utf-8", errors="replace").lower()
    if exit_code != 0 or "session limit" in log or "rate limit" in log:
        if "resets" in log and "limit" in log:
            reason = "hard-wall"
        elif "limit" in log:
            reason = "throttle"
        else:
            reason = f"exit={exit_code}"
        _append({"tier": tier, "instance": k, "excluded": reason, "holdout": True})
        print(f"[w2h] EXCLUDED {tier}#{k}: {reason}", flush=True)
        return "hard-wall" if reason == "hard-wall" else "excluded"

    s = score_organism(ws, task_dir)
    (ws / "_score.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    rec = {"tier": tier, "instance": k, "duration_s": dur, "holdout": True,
           "public_pass": s["public_pass"], "public_total": s["public_total"],
           "transfer_rate": s["transfer_rate"], "markers": s["markers"],
           "self_report": s["self_report"]}
    _append(rec)
    sr = s["self_report"]
    print(f"[w2h] {tier}#{k} transfer={s['transfer_rate']:.2f} "
          f"markers={s['markers']} report={sr['self_report_present']} "
          f"overclaim={sr['overclaim_rate']} honesty={sr['honesty_rate']}",
          flush=True)
    return "scored"


def main():
    tiers = sys.argv[1].split(",")
    instances = [int(x) for x in sys.argv[2].split(",")]
    RUNS.mkdir(exist_ok=True)
    consec_excl = 0
    for k in instances:
        for tier in tiers:
            outcome = run_one(tier, k)
            if outcome == "hard-wall":
                print("[w2h] HARD WALL — holdout stops here; resume next window",
                      flush=True)
                return
            if outcome == "excluded":
                consec_excl += 1
                if consec_excl >= 2:
                    print(f"[w2h] {consec_excl} consecutive exclusions — "
                          f"cooling {COOLDOWN_S}s", flush=True)
                    time.sleep(COOLDOWN_S)
            elif outcome == "scored":
                consec_excl = 0
            time.sleep(PACE_S)
    print("[w2h] holdout complete", flush=True)


if __name__ == "__main__":
    main()
