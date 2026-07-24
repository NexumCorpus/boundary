#!/usr/bin/env python3
"""Trusted Boundary adapter for causal-xenosoma bundles.

This is a verifier, not an Atlas status adapter.  It independently checks the
commit/reveal and anti-gaming invariants before emitting a source-bound receipt.
"""
import hashlib, json, secrets, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERIFIER = "boundary-xenosoma-v1"
PROTOCOL = "boundary-xenosoma-receipt-v1"
ROOT = Path(__file__).resolve().parents[1]

def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha(value):
    return "sha256:" + hashlib.sha256(canon(value).encode()).hexdigest()

def head():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

def receipt(bundle):
    now = datetime.now(timezone.utc)
    checks = []
    metrics = bundle.get("metrics") or {}
    commitment = bundle.get("commitment") or {}
    forbidden = {"secret", "mapping", "holdoutSeeds", "hiddenMechanism"}
    leaked = sorted(k for k in forbidden if k in commitment)
    checks += [
        ("commitment_order", metrics.get("commitmentBeforePerturbation") is True),
        ("commitment_verified", metrics.get("commitmentVerified") is True),
        ("hidden_secret_absent", not leaked),
        ("generator_grader_disjoint", bundle.get("generator") != bundle.get("grader")),
        ("observational_baseline_zero", metrics.get("baselineInformationGain") == 0),
        ("class_diversity", metrics.get("trialClassDiversity") == 2 and metrics.get("holdoutClassDiversity") == 2),
        ("holdout_reproduced", metrics.get("verificationYield") == 1),
        ("ordinary_dialogue_not_promotion", not bundle.get("promotion") and bundle.get("status") not in {"promoted", "eligible"}),
    ]
    anchors = sorted(set(bundle.get("evidenceAnchors") or []))
    holdout = sorted(set(bundle.get("holdoutAnchors") or []))
    falsifiers = [name for name, ok in checks if not ok]
    payload = {
        "verifier": VERIFIER, "protocolVersion": PROTOCOL, "verifierSourceHead": head(),
        "experimentHash": bundle.get("experimentHash"),
        "commitmentRecordHash": bundle.get("commitmentRecordHash"),
        "perturbationRecordHash": bundle.get("perturbationRecordHash"),
        "evidenceAnchors": anchors, "holdoutAnchors": holdout,
        "nonce": secrets.token_hex(32),
        "measurements": {"checks": {name: ok for name, ok in checks}, "metrics": metrics},
        "verdict": "pass" if not falsifiers else "fail",
        "falsifiers": falsifiers, "issuedAt": now.isoformat(),
        "expiry": (now + timedelta(days=7)).isoformat(),
        "generator": bundle.get("generator"), "grader": bundle.get("grader"),
    }
    return {**payload, "recordHash": sha(payload)}

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: verify_xenosoma_receipt.py bundle.json")
    print(json.dumps(receipt(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))), sort_keys=True))
