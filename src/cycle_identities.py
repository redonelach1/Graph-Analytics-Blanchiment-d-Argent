"""
cycle_identities.py — Canonical Cycle & Alert Identity Generation.

Implements Sections 6.3 and 6.4 of project_plan_and_specifications.md:
- cycle_id = SHA256(canonical JSON array of sorted transaction IDs)
- alert_id = SHA256(canonical JSON [rule_id, rule_version, cycle_id])
- Deterministic risk classification: HIGH, MEDIUM, LOW
"""

import hashlib
import json
from typing import Any, Dict, List, Tuple


def compute_cycle_id(transaction_ids: List[str]) -> str:
    """
    Computes deterministic SHA256 hash of sorted transaction IDs.
    Ensures that identical cycles discovered in different orders or
    across overlapping windows produce the exact same cycle_id.
    """
    cleaned_ids = sorted([str(tid).strip() for tid in transaction_ids])
    canonical_json = json.dumps(cleaned_ids, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_alert_id(
    rule_id: str,
    rule_version: int,
    cycle_id: str
) -> str:
    """
    Computes deterministic SHA256 hash of [rule_id, rule_version, cycle_id].
    """
    payload = [str(rule_id), int(rule_version), str(cycle_id)]
    canonical_json = json.dumps(payload, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def classify_risk(
    amounts: List[float],
    config: Dict[str, Any]
) -> Tuple[str, List[str]]:
    """
    Classifies risk level based on amounts:
    - HIGH: min_amount >= high_min_amount AND max_amount / min_amount <= high_ratio_tolerance
    - MEDIUM: min_amount >= medium_min_amount
    - LOW: other qualifying cycles

    Returns (risk_level, reason_codes)
    """
    risk_cfg = config.get("risk", {})
    high_min = float(risk_cfg.get("high_min_amount", 100000.0))
    ratio_tol = float(risk_cfg.get("high_ratio_tolerance", 2.0))
    medium_min = float(risk_cfg.get("medium_min_amount", 10000.0))

    if not amounts:
        return "LOW", ["DIRECTED_TRIANGLE", "NO_AMOUNTS"]

    min_amt = min(amounts)
    max_amt = max(amounts)
    ratio = (max_amt / min_amt) if min_amt > 0 else float("inf")

    reasons = ["DIRECTED_TRIANGLE", "SAME_CURRENCY"]

    if min_amt >= high_min and ratio <= ratio_tol:
        reasons.extend(["HIGH_VALUE_THRESHOLD_MET", f"AMOUNT_RATIO_TOLERANT_{ratio:.2f}"])
        return "HIGH", reasons
    elif min_amt >= medium_min:
        reasons.append("MEDIUM_VALUE_THRESHOLD_MET")
        return "MEDIUM", reasons
    else:
        reasons.append("LOW_VALUE_CYCLE")
        return "LOW", reasons

