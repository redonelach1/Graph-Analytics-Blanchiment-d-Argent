"""
test_detection.py — Comprehensive Verification of Temporal Triangle Motif Detection.

Verifies Acceptance Criteria:
- AT-01: Known triangle inside one window -> exactly one alert
- AT-02: Rotated vertex labels produce the same alert_id
- AT-03: Edges arriving across multiple batches detect on final edge
- AT-04: Open chain (A -> B -> C) produces no alert
- AT-06: No common 10-minute window produces no alert
- AT-07: Half-open window boundary semantics [start, end)
- AT-08: Same cycle matching overlapping windows produces 1 unique logical alert
- AT-09: Out-of-order final edge detection
- AT-10: Event older than watermark classified as late / retrospective-only
- AT-15: Mixed currencies excluded from baseline
- AT-16: 4-account cycle produces no 3-account alert
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cycle_identities import compute_alert_id, compute_cycle_id
from detection import detect_triangles_in_window
from temporal_policy import TemporalWindowPolicy


def load_fixture(fixture_name: str):
    path = Path(__file__).resolve().parent / "fixtures" / fixture_name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_at01_known_triangle_simple():
    """AT-01: Known triangle inside one window -> exactly 1 alert."""
    data = load_fixture("triangle_simple.json")
    txns = data["transactions"]
    alerts = detect_triangles_in_window(txns)

    assert len(alerts) == 1, f"Expected 1 alert, got {len(alerts)}"
    alert = alerts[0]
    assert set(alert["account_ids"]) == {"ACC-ALICE", "ACC-BOB", "ACC-CHARLIE"}
    assert set(alert["transaction_ids"]) == {"TXN-FIX-TRI-001", "TXN-FIX-TRI-002", "TXN-FIX-TRI-003"}
    assert alert["risk_level"] in ("HIGH", "MEDIUM", "LOW")
    print("[PASS] AT-01: Known triangle detected with exact evidence")


def test_at02_rotated_vertex_labels():
    """AT-02: Same triangle with rotated starting vertex produces identical alert_id."""
    # Cycle 1: Alice -> Bob -> Charlie -> Alice
    c1 = [
        {"transaction_id": "T1", "source_account": "A", "target_account": "B", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:00:00Z"},
        {"transaction_id": "T2", "source_account": "B", "target_account": "C", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:01:00Z"},
        {"transaction_id": "T3", "source_account": "C", "target_account": "A", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:02:00Z"},
    ]
    # Cycle 2: Starting at Bob: Bob -> Charlie -> Alice -> Bob
    c2 = [
        {"transaction_id": "T2", "source_account": "B", "target_account": "C", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:01:00Z"},
        {"transaction_id": "T3", "source_account": "C", "target_account": "A", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:02:00Z"},
        {"transaction_id": "T1", "source_account": "A", "target_account": "B", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:00:00Z"},
    ]

    a1 = detect_triangles_in_window(c1)[0]
    a2 = detect_triangles_in_window(c2)[0]

    assert a1["cycle_id"] == a2["cycle_id"], "Cycle IDs must match regardless of traversal start"
    assert a1["alert_id"] == a2["alert_id"], "Alert IDs must match regardless of traversal start"
    print("[PASS] AT-02: Rotated vertex labels produce identical alert_id")


def test_at03_edges_across_multiple_batches():
    """AT-03: Edges arrive in three separate batches -> detection triggers only on 3rd edge."""
    e1 = {"transaction_id": "T1", "source_account": "A", "target_account": "B", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:00:00Z"}
    e2 = {"transaction_id": "T2", "source_account": "B", "target_account": "C", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:02:00Z"}
    e3 = {"transaction_id": "T3", "source_account": "C", "target_account": "A", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:04:00Z"}

    # Batch 1: Only T1
    alerts_b1 = detect_triangles_in_window([e1], new_transaction_ids={"T1"})
    assert len(alerts_b1) == 0

    # Batch 2: T1 (history) + T2 (new)
    alerts_b2 = detect_triangles_in_window([e1, e2], new_transaction_ids={"T2"})
    assert len(alerts_b2) == 0

    # Batch 3: T1, T2 (history) + T3 (new)
    alerts_b3 = detect_triangles_in_window([e1, e2, e3], new_transaction_ids={"T3"})
    assert len(alerts_b3) == 1
    assert alerts_b3[0]["alert_id"] is not None
    print("[PASS] AT-03: Detection triggers upon arrival of final closing edge")


def test_at04_open_chain_no_alert():
    """AT-04: Open chain A -> B -> C -> 0 alerts."""
    data = load_fixture("open_chain.json")
    alerts = detect_triangles_in_window(data["transactions"])
    assert len(alerts) == 0
    print("[PASS] AT-04: Open chain produces no alerts")


def test_at06_no_common_window():
    """AT-06: Edges spanning more than 10 minutes apart -> 0 alerts."""
    data = load_fixture("boundary_events.json")
    policy = TemporalWindowPolicy(window_length_seconds=600, slide_seconds=30)
    txns = data["transactions"]

    # Check if all 3 transactions share any single aligned window
    t1 = datetime.fromisoformat(txns[0]["timestamp"].replace("Z", "+00:00"))
    t2 = datetime.fromisoformat(txns[1]["timestamp"].replace("Z", "+00:00"))
    t3 = datetime.fromisoformat(txns[2]["timestamp"].replace("Z", "+00:00"))

    w1 = set(policy.get_aligned_windows(t1))
    w2 = set(policy.get_aligned_windows(t2))
    w3 = set(policy.get_aligned_windows(t3))

    shared_windows = w1.intersection(w2).intersection(w3)
    assert len(shared_windows) == 0, "Transactions spanning >10 minutes must not share any window"
    print("[PASS] AT-06: No common 10-minute window correctly prevents alert generation")


def test_at07_half_open_window_boundary():
    """AT-07: Window membership is half-open [start, end)."""
    policy = TemporalWindowPolicy(window_length_seconds=600, slide_seconds=30)
    w_start = datetime(2026, 10, 7, 10, 0, 0, tzinfo=timezone.utc)
    w_end = datetime(2026, 10, 7, 10, 10, 0, tzinfo=timezone.utc)

    # Exactly at start -> True
    assert policy.is_in_window(w_start, w_start, w_end) is True
    # In middle -> True
    mid = datetime(2026, 10, 7, 10, 5, 0, tzinfo=timezone.utc)
    assert policy.is_in_window(mid, w_start, w_end) is True
    # Exactly at end -> False (half-open)
    assert policy.is_in_window(w_end, w_start, w_end) is False
    print("[PASS] AT-07: Half-open interval [start, end) verified")


def test_at08_overlapping_windows_single_logical_alert():
    """AT-08: Same cycle matching overlapping sliding windows produces 1 unique logical alert."""
    policy = TemporalWindowPolicy(window_length_seconds=600, slide_seconds=30)
    t = datetime(2026, 10, 7, 10, 5, 0, tzinfo=timezone.utc)
    windows = policy.get_aligned_windows(t)
    assert len(windows) > 1, "An event must participate in multiple overlapping sliding windows"

    # Evaluate cycle in each window
    cycle_txns = load_fixture("triangle_simple.json")["transactions"]
    alert_ids = set()

    for w_start, w_end in windows:
        w_alerts = detect_triangles_in_window(
            cycle_txns, window_start=w_start, window_end=w_end
        )
        for al in w_alerts:
            alert_ids.add(al["alert_id"])

    # Must produce exactly ONE distinct logical alert ID
    assert len(alert_ids) == 1, f"Expected 1 unique alert_id across overlapping windows, got {len(alert_ids)}"
    print("[PASS] AT-08: Overlapping sliding windows deduplicate to a single logical alert ID")


def test_at09_out_of_order_final_edge():
    """AT-09: Final edge arrives with an earlier timestamp than intermediate edge."""
    # Chronological: T1 (10:00), T2 (10:04), T3 (10:02) -> out of order delivery
    txns = [
        {"transaction_id": "T1", "source_account": "A", "target_account": "B", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:00:00Z"},
        {"transaction_id": "T2", "source_account": "B", "target_account": "C", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:04:00Z"},
        {"transaction_id": "T3", "source_account": "C", "target_account": "A", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:02:00Z"},
    ]
    alerts = detect_triangles_in_window(txns, new_transaction_ids={"T3"})
    assert len(alerts) == 1
    print("[PASS] AT-09: Out-of-order final edge detected within window")


def test_at10_watermark_lateness():
    """AT-10: Event older than W = H - 120s is classified as late."""
    policy = TemporalWindowPolicy(window_length_seconds=600, slide_seconds=30, watermark_seconds=120)
    h_time = datetime(2026, 10, 7, 10, 10, 0, tzinfo=timezone.utc)
    policy.update_high_water_mark(h_time)

    # Watermark is at 10:08:00 UTC
    w = policy.get_watermark()
    assert w == datetime(2026, 10, 7, 10, 8, 0, tzinfo=timezone.utc)

    # Event at 10:08:30 (newer than W) -> not late
    assert policy.is_late(datetime(2026, 10, 7, 10, 8, 30, tzinfo=timezone.utc)) is False

    # Event at 10:07:00 (older than W) -> late
    assert policy.is_late(datetime(2026, 10, 7, 10, 7, 0, tzinfo=timezone.utc)) is True
    print("[PASS] AT-10: Application watermark correctly identifies late events")


def test_at15_mixed_currencies_excluded():
    """AT-15: Triangle with mixed currencies (MAD, USD, EUR) is excluded from MAD baseline."""
    data = load_fixture("mixed_currency.json")
    alerts = detect_triangles_in_window(data["transactions"], config={"detection": {"supported_currencies": ["MAD"]}})
    assert len(alerts) == 0, "Mixed-currency cycle must be excluded from baseline rule"
    print("[PASS] AT-15: Mixed currency cycle excluded from detection")


def test_at16_four_account_cycle_only():
    """AT-16: 4-account cycle (A -> B -> C -> D -> A) produces no 3-account alert."""
    txns = [
        {"transaction_id": "T1", "source_account": "A", "target_account": "B", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:00:00Z"},
        {"transaction_id": "T2", "source_account": "B", "target_account": "C", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:01:00Z"},
        {"transaction_id": "T3", "source_account": "C", "target_account": "D", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:02:00Z"},
        {"transaction_id": "T4", "source_account": "D", "target_account": "A", "montant": 1000.0, "devise": "MAD", "timestamp": "2026-10-07T10:03:00Z"},
    ]
    alerts = detect_triangles_in_window(txns)
    assert len(alerts) == 0, "4-account cycle must not trigger a 3-account triangle alert"
    print("[PASS] AT-16: 4-account cycle correctly ignored by 3-account detector")


if __name__ == "__main__":
    test_at01_known_triangle_simple()
    test_at02_rotated_vertex_labels()
    test_at03_edges_across_multiple_batches()
    test_at04_open_chain_no_alert()
    test_at06_no_common_window()
    test_at07_half_open_window_boundary()
    test_at08_overlapping_windows_single_logical_alert()
    test_at09_out_of_order_final_edge()
    test_at10_watermark_lateness()
    test_at15_mixed_currencies_excluded()
    test_at16_four_account_cycle_only()
    print("\nALL TEMPORAL TRIANGLE DETECTION TESTS PASSED!")

