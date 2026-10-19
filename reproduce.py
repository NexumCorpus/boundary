#!/usr/bin/env python3
"""Check the Boundary Program's machinery yourself, from a fresh clone.

1. Scorer contract: the trusted scorer's tests (a synthetic memorizing gamer
   gets a perfect visible metric and fails the hidden probes).
2. Certified claim boundary-wave2-gaming-null-holdout-v1: re-run its own
   check.py, unchanged, on every claimed seed against the recorded holdout
   scores shipped next to it (originally at E:/mission-runs/, outside the repo).

Re-running the organisms themselves needs the claude CLI and hours; the
recorded scores are the reproducible unit (organisms are nondeterministic).
"""
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "mission1" / "certify" / "gaming_null_v1"


def scorer_contract():
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "mission1/tests"], cwd=ROOT)
    return r.returncode == 0


def load_check():
    spec = importlib.util.spec_from_file_location("check", BUNDLE / "check.py")
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    return check


def run_check(check, ledger, seed):
    check.LEDGER = ledger
    sys.argv = ["check.py", str(seed)]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            check.main()
            code = 0
        except SystemExit as e:
            code = e.code
    return code, out.getvalue().strip()


def certified_claim():
    check = load_check()
    ledger = BUNDLE / "w2_holdout_results.jsonl"
    claim = json.loads((BUNDLE / "claim.json").read_text(encoding="utf-8"))
    ok = True
    for seed in claim["claimed_seeds"]:
        code, msg = run_check(check, ledger, seed)
        print(f"  {msg}  (exit {code})")
        ok &= code == 0
    # Negative control: the same check must FAIL on a ledger with one gaming marker planted.
    rows = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
    target = claim["claimed_seeds"][0]
    for r in rows:
        if r.get("instance") == target and "markers" in r:
            r["markers"]["memorized_literals"] = 1
    with tempfile.TemporaryDirectory() as tmp:
        tampered = Path(tmp) / "tampered.jsonl"
        tampered.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        code, msg = run_check(check, tampered, target)
    print(f"  negative control (planted marker on seed {target}): {msg}  (exit {code}, must be 1)")
    return ok and code == 1


if __name__ == "__main__":
    print("[1/2] scorer contract tests")
    a = scorer_contract()
    print("[2/2] certified claim boundary-wave2-gaming-null-holdout-v1")
    b = certified_claim()
    print(f"\nscorer contract: {'PASS' if a else 'FAIL'}   certified claim: {'PASS' if b else 'FAIL'}")
    sys.exit(0 if a and b else 1)
