"""
detection.py — Temporal Triangle Cycle Detection Engine.

Implements Sections 6.2, 6.3, and 6.4 of project_plan_and_specifications.md:
- Motif: (a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)
- Mandatory filters:
  * a, b, c have distinct account IDs
  * e1, e2, e3 have distinct transaction IDs
  * All edges belong to the same aligned window
  * All edges have the same supported currency
  * No self-transfer edges
  * At least one edge is newly accepted in the current operation
- Outputs authoritative fraud_alerts rows and projections for anomaly_vertices & anomaly_edges
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from src.cycle_identities import classify_risk, compute_alert_id, compute_cycle_id
    from src.temporal_policy import TemporalWindowPolicy
    from src.validation import parse_iso_timestamp
except ImportError:
    from cycle_identities import classify_risk, compute_alert_id, compute_cycle_id
    from temporal_policy import TemporalWindowPolicy
    from validation import parse_iso_timestamp

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql import functions as F
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


RULE_ID = "TEMPORAL_TRIANGLE"
RULE_VERSION = 1


def detect_triangles_in_window(
    window_transactions: List[Dict[str, Any]],
    new_transaction_ids: Optional[Set[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Pure Python cycle detection for finding directed triangles: A -> B -> C -> A.
    Can be used directly on in-memory batches, unit test fixtures, or fallback execution.

    :param window_transactions: All transactions active in this window.
    :param new_transaction_ids: Set of transaction IDs newly arrived in this batch.
    :param config: System configuration dictionary.
    :param window_start: Aligned window start timestamp.
    :param window_end: Aligned window end timestamp.
    :return: List of alert records.
    """
    if config is None:
        config = {}
    if new_transaction_ids is None:
        new_transaction_ids = {t["transaction_id"] for t in window_transactions}

    supported_currencies = set(
        config.get("detection", {}).get("supported_currencies", ["MAD"])
    )

    # Build adjacency: src -> list of (dst, transaction)
    adj: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for txn in window_transactions:
        src = txn.get("src", txn.get("source_account", ""))
        dst = txn.get("dst", txn.get("target_account", ""))
        curr = txn.get("currency", txn.get("devise", "MAD"))

        # Skip self-transfers or unsupported currencies
        if src == dst:
            continue
        if curr not in supported_currencies:
            continue

        adj[src].append(txn)

    discovered_alerts: List[Dict[str, Any]] = []
    seen_cycle_ids: Set[str] = set()

    # Search for directed triangles: A -> B -> C -> A
    for a in list(adj.keys()):
        for e1 in adj[a]:
            b = e1.get("dst", e1.get("target_account", ""))
            if b == a:
                continue

            for e2 in adj[b]:
                c = e2.get("dst", e2.get("target_account", ""))
                # a, b, c must be distinct
                if c == a or c == b:
                    continue

                for e3 in adj[c]:
                    d = e3.get("dst", e3.get("target_account", ""))
                    # Must close back to A
                    if d != a:
                        continue

                    # Distinct transaction IDs
                    t1_id = e1["transaction_id"]
                    t2_id = e2["transaction_id"]
                    t3_id = e3["transaction_id"]
                    if len({t1_id, t2_id, t3_id}) < 3:
                        continue

                    # Currency must be identical
                    c1 = e1.get("currency", e1.get("devise"))
                    c2 = e2.get("currency", e2.get("devise"))
                    c3 = e3.get("currency", e3.get("devise"))
                    if not (c1 == c2 == c3):
                        continue

                    # At least one edge must be new in this operation
                    has_new_edge = bool({t1_id, t2_id, t3_id}.intersection(new_transaction_ids))
                    if not has_new_edge:
                        continue

                    # Compute canonical identities
                    txn_ids = [t1_id, t2_id, t3_id]
                    cycle_id = compute_cycle_id(txn_ids)

                    if cycle_id in seen_cycle_ids:
                        continue
                    seen_cycle_ids.add(cycle_id)

                    alert_id = compute_alert_id(RULE_ID, RULE_VERSION, cycle_id)

                    amounts = [
                        float(e1.get("amount", e1.get("montant", 0.0))),
                        float(e2.get("amount", e2.get("montant", 0.0))),
                        float(e3.get("amount", e3.get("montant", 0.0))),
                    ]
                    risk_level, reason_codes = classify_risk(amounts, config)

                    # Extract timestamps
                    ts1 = parse_iso_timestamp(str(e1.get("event_time", e1.get("timestamp"))))
                    ts2 = parse_iso_timestamp(str(e2.get("event_time", e2.get("timestamp"))))
                    ts3 = parse_iso_timestamp(str(e3.get("event_time", e3.get("timestamp"))))
                    event_min = min(ts1, ts2, ts3)
                    event_max = max(ts1, ts2, ts3)

                    now_utc = datetime.now(timezone.utc)
                    first_detected_at = now_utc.strftime("%Y-%m-%d %H:%M:%S")

                    evidence = {
                        "accounts": [a, b, c],
                        "edges": [
                            {"transaction_id": t1_id, "src": a, "dst": b, "amount": amounts[0], "currency": c1, "time": ts1.isoformat()},
                            {"transaction_id": t2_id, "src": b, "dst": c, "amount": amounts[1], "currency": c2, "time": ts2.isoformat()},
                            {"transaction_id": t3_id, "src": c, "dst": a, "amount": amounts[2], "currency": c3, "time": ts3.isoformat()},
                        ],
                        "matching_window": {
                            "start": window_start.isoformat() if window_start else None,
                            "end": window_end.isoformat() if window_end else None,
                        }
                    }

                    alert_record = {
                        "alert_id": alert_id,
                        "cycle_id": cycle_id,
                        "rule_id": RULE_ID,
                        "rule_version": RULE_VERSION,
                        "risk_level": risk_level,
                        "evidence_json": json.dumps(evidence),
                        "reason_codes": reason_codes,
                        "first_detected_at": first_detected_at,
                        "event_min": event_min.strftime("%Y-%m-%d %H:%M:%S"),
                        "event_max": event_max.strftime("%Y-%m-%d %H:%M:%S"),
                        "account_ids": [a, b, c],
                        "transaction_ids": txn_ids,
                        "currency": c1,
                        "dt": now_utc.strftime("%Y-%m-%d"),
                    }
                    discovered_alerts.append(alert_record)

    return discovered_alerts


def detect_triangles_graphframes(
    graph_frame: Any,
    new_txn_ids: Set[str],
    config: Dict[str, Any],
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Executes motif finding in PySpark GraphFrames:
    g.find("(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)")
    Applies mandatory vertex and edge equality filters.
    """
    if not PYSPARK_AVAILABLE:
        raise RuntimeError("PySpark GraphFrames is required for detect_triangles_graphframes.")

    # 1. Execute motif query
    motifs = graph_frame.find("(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)")

    # 2. Distinct vertices and edges
    filtered = motifs.filter(
        (F.col("a.id") != F.col("b.id"))
        & (F.col("b.id") != F.col("c.id"))
        & (F.col("a.id") != F.col("c.id"))
        & (F.col("e1.transaction_id") != F.col("e2.transaction_id"))
        & (F.col("e2.transaction_id") != F.col("e3.transaction_id"))
        & (F.col("e1.transaction_id") != F.col("e3.transaction_id"))
        & (F.col("e1.currency") == F.col("e2.currency"))
        & (F.col("e2.currency") == F.col("e3.currency"))
    )

    rows = filtered.collect()
    alerts = []
    seen_cycles = set()

    for r in rows:
        t1, t2, t3 = r.e1.transaction_id, r.e2.transaction_id, r.e3.transaction_id
        # Check at least one new edge
        if not ({t1, t2, t3}.intersection(new_txn_ids)):
            continue

        cycle_id = compute_cycle_id([t1, t2, t3])
        if cycle_id in seen_cycles:
            continue
        seen_cycles.add(cycle_id)

        alert_id = compute_alert_id(RULE_ID, RULE_VERSION, cycle_id)
        amounts = [float(r.e1.amount), float(r.e2.amount), float(r.e3.amount)]
        risk_level, reasons = classify_risk(amounts, config)

        now_utc = datetime.now(timezone.utc)
        evidence = {
            "accounts": [r.a.id, r.b.id, r.c.id],
            "edges": [
                {"transaction_id": t1, "src": r.e1.src, "dst": r.e1.dst, "amount": amounts[0], "currency": r.e1.currency, "time": str(r.e1.event_time)},
                {"transaction_id": t2, "src": r.e2.src, "dst": r.e2.dst, "amount": amounts[1], "currency": r.e2.currency, "time": str(r.e2.event_time)},
                {"transaction_id": t3, "src": r.e3.src, "dst": r.e3.dst, "amount": amounts[2], "currency": r.e3.currency, "time": str(r.e3.event_time)},
            ],
            "matching_window": {
                "start": window_start.isoformat() if window_start else None,
                "end": window_end.isoformat() if window_end else None,
            }
        }

        alerts.append({
            "alert_id": alert_id,
            "cycle_id": cycle_id,
            "rule_id": RULE_ID,
            "rule_version": RULE_VERSION,
            "risk_level": risk_level,
            "evidence_json": json.dumps(evidence),
            "reason_codes": reasons,
            "first_detected_at": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "event_min": min(str(r.e1.event_time), str(r.e2.event_time), str(r.e3.event_time)),
            "event_max": max(str(r.e1.event_time), str(r.e2.event_time), str(r.e3.event_time)),
            "account_ids": [r.a.id, r.b.id, r.c.id],
            "transaction_ids": [t1, t2, t3],
            "currency": r.e1.currency,
            "dt": now_utc.strftime("%Y-%m-%d"),
        })

    return alerts

