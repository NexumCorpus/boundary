"""Recompute a submitted v1 transcript; not proof of independent execution."""
import hashlib
import json


def ordered_hash(value):
    data = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


def audit(bundle):
    checks = {}
    try:
        commitment = bundle["commitment"]
        revealed = bundle["revealedPayload"]
        trials = bundle["trials"]
        holdout = bundle["holdout"]
        seeds = revealed["trialSeeds"]
        unseen = revealed["holdoutSeeds"]
        mapping = revealed["mapping"]
        checks["protocol"] = commitment["protocolVersion"] == revealed["protocolVersion"] == "causal-xenosoma-commit-reveal-v1"
        checks["commitment_recomputed"] = ordered_hash(revealed) == commitment["commitmentHash"]
        checks["nonce"] = isinstance(revealed["nonce"], str) and len(bytes.fromhex(revealed["nonce"])) == 16
        checks["corpus"] = (len(seeds) >= 4 and len(unseen) == 2
            and all(type(seed) is int for seed in seeds + unseen)
            and len(set(seeds + unseen)) == len(seeds + unseen)
            and set(mapping) == {str(seed) for seed in seeds + unseen})
        checks["trial_membership"] = [row["seed"] for row in trials] == seeds
        checks["holdout_membership"] = [row["surface"]["seed"] for row in holdout] == unseen
        checks["mapping_classes"] = set(mapping.values()) == {"alpha", "beta"}
        checks["trial_replay"] = all(
            row["intervention"]["output"] == row["intervention"]["revealedMechanism"] == mapping[str(row["seed"])]
            and row["intervention"]["commitmentHash"] == commitment["commitmentHash"]
            and row["intervention"]["pass"] is True
            and row["surface"]["seed"] == row["seed"]
            and row["surface"]["observation"] == row["baseline"]["output"] == "stable"
            and row["baseline"]["intervened"] is False
            and row["baseline"]["informationGain"] == 0
            and row["posterior"] == ([1, 0] if mapping[str(row["seed"])] == "alpha" else [0, 1])
            for row in trials)
        checks["holdout_replay"] = all(
            row["intervention"]["output"] == mapping[str(row["surface"]["seed"])]
            and row["intervention"]["seed"] == row["surface"]["seed"]
            and row["intervention"]["commitmentHash"] == commitment["commitmentHash"]
            and row["intervention"]["pass"] is True for row in holdout)
        checks["trial_anchors_recomputed"] = all(row["evidenceAnchor"] == ordered_hash({
            "seed": row["seed"], "surface": row["surface"], "intervention": row["intervention"],
            "commitmentHash": commitment["commitmentHash"]}) for row in trials)
        checks["holdout_anchors_recomputed"] = all(row["evidenceAnchor"] == ordered_hash({
            "holdoutIndex": row["holdoutIndex"], "surface": row["surface"], "measured": row["intervention"],
            "commitmentHash": commitment["commitmentHash"]}) for row in holdout)
        checks["anchor_lists"] = (sorted(bundle["evidenceAnchors"]) == sorted(row["evidenceAnchor"] for row in trials)
            and sorted(bundle["holdoutAnchors"]) == sorted(row["evidenceAnchor"] for row in holdout))
        checks["experiment_recomputed"] = bundle["experimentHash"] == ordered_hash({key: bundle[key] for key in
            ("genome", "hypotheses", "perturbation", "commitment", "trials", "holdout", "metrics")})
        checks["class_diversity_recomputed"] = (len({mapping[str(seed)] for seed in seeds}) == 2
            and len({mapping[str(seed)] for seed in unseen}) == 2)
        metrics = bundle["metrics"]
        checks["core_metrics_recomputed"] = (metrics["informationGain"] == 1
            and metrics["baselineInformationGain"] == 0 and metrics["error"] == 0
            and metrics["verificationYield"] == 1
            and metrics["trialClassDiversity"] == len({row["intervention"]["output"] for row in trials})
            and metrics["holdoutClassDiversity"] == len({row["intervention"]["output"] for row in holdout}))
    except (KeyError, TypeError, ValueError, OverflowError):
        checks["transcript_shape"] = False
    return checks
