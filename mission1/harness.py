"""Organism dispatch harness for Mission 1.

One organism = one fresh workspace (task skeleton + brief) + one CLI agent run
under a single condition directive. The harness only dispatches and collects;
scoring is scorer.py (trusted, organism-blind), invoked separately.

Usage:
  python harness.py pilot                    # one S3 organism (plumbing check)
  python harness.py run S2 3                 # condition S2, instance 3
  python harness.py score runs/S2_03         # score a collected workspace

Budget note (constitution sec 6.6): each organism is one `claude -p` call on
the subscription; quota is the scarce resource — sweeps are spread across
sessions by design.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from conditions import CONDITIONS

HERE = Path(__file__).resolve().parent
TASK = HERE / "tasks" / "task_a"
RUNS = HERE / "runs"
ORGANISM_TIMEOUT_S = 900
MODEL = "sonnet"


def build_workspace(condition: str, instance: int) -> Path:
    ws = RUNS / f"{condition}_{instance:02d}"
    if ws.exists():
        raise SystemExit(f"workspace exists: {ws} (instances are never reused)")
    shutil.copytree(TASK / "skeleton", ws)
    shutil.copy2(TASK / "brief.md", ws / "brief.md")
    return ws


def run_organism(condition: str, instance: int) -> Path:
    directive = CONDITIONS[condition]
    ws = build_workspace(condition, instance)
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("claude CLI not on PATH")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [claude, "-p", directive, "--model", MODEL,
             "--permission-mode", "bypassPermissions"],
            cwd=str(ws), capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=ORGANISM_TIMEOUT_S)
        exit_code, out = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        exit_code, out = -1, "(organism timed out)"
    (ws / "_organism.log").write_text(out, encoding="utf-8")
    (ws / "_meta.json").write_text(json.dumps({
        "condition": condition, "instance": instance, "model": MODEL,
        "directive": directive, "duration_s": round(time.time() - t0, 1),
        "exit": exit_code, "collected_utc": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=1), encoding="utf-8")
    print(f"[harness] {condition}#{instance} done in "
          f"{time.time() - t0:.0f}s exit={exit_code} -> {ws}")
    return ws


def score(ws: Path):
    sys.path.insert(0, str(HERE))
    from scorer import score_organism
    result = score_organism(ws, TASK / "probes")
    (Path(ws) / "_score.json").write_text(json.dumps(result, indent=1),
                                          encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ("public_pass", "public_total", "probe_pass",
                       "probe_total", "transfer_rate", "markers")}, indent=1))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    if mode == "pilot":
        ws = run_organism("S3", 0)
        score(ws)
    elif mode == "run":
        run_organism(sys.argv[2], int(sys.argv[3]))
    elif mode == "score":
        score(Path(sys.argv[2]))
    else:
        raise SystemExit(f"unknown mode {mode}")
