#!/usr/bin/env python3
"""
test_idle_stream.py — Acceptance Test AT-21: Idle Stream Watermark Non-Advancement.

Verifies Section 12 Acceptance Criteria:
AT-21: Watermark MUST NOT advance in the absence of new incoming transactions with higher
timestamps. The 2-minute delay must be relative to observed event time, not wall-clock time.

Setup:
- Ingest batch with max event_time = T0.
- Let stream sit idle (simulate wall-clock time passing).
- Ingest transaction with event_time = T0 - 30 seconds.
- Verification: Late transaction MUST still be accepted into silver_transactions because
  watermark is at T0 - 2 minutes, NOT advanced by wall-clock time.
"""

import sys
import os
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.temporal_policy import TemporalWindowPolicy
from src.validation import validate_transaction, ValidationOutcome


def test_at_21_idle_stream_watermark_non_advancement():
    """AT-21: Watermark MUST NOT advance without new event timestamps."""
    policy = TemporalWindowPolicy(
        window_length_seconds=600,
        slide_seconds=30,
        watermark_seconds=120
    )

    t0 = datetime(2026, 11, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    # 1. Establish initial high water mark at T0
    policy.update_high_water_mark(t0)
    w0 = policy.get_watermark()
    expected_w0 = t0 - timedelta(seconds=120)  # 11:58:00
    assert w0 == expected_w0, f"Watermark should be T0 - 120s, got {w0}"

    # 2. Simulate stream idle period (simulate wall-clock time passing)
    # Note: we do NOT call update_high_water_mark because no new records arrived
    time.sleep(0.1)

    w_after_idle = policy.get_watermark()
    assert w_after_idle == expected_w0, (
        f"Watermark advanced during idle stream! Expected {expected_w0}, got {w_after_idle}"
    )

    # 3. Ingest transaction with event_time = T0 - 30s (11:59:30)
    t_late = t0 - timedelta(seconds=30)
    is_late = policy.is_late(t_late)
    assert not is_late, (
        f"Transaction at T0 - 30s should NOT be marked late (W = {expected_w0}, Txn = {t_late})"
    )

    # 4. Verify transaction validation acceptance
    txn = {
        "schema_version": 1,
        "transaction_id": "TXN-IDLE-001",
        "source_account": "ACC-IDLE-A",
        "target_account": "ACC-IDLE-B",
        "montant": 1000.0,
        "devise": "MAD",
        "timestamp": t_late.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type_operation": "VIREMENT"
    }
    outcome, errors, norm = validate_transaction(txn, ingest_time=t0)
    assert outcome == ValidationOutcome.VALID, f"Expected VALID status, got {outcome} (errors: {errors})"

    # 5. Ingest truly expired transaction at T0 - 150s (11:57:30 < 11:58:00)
    t_expired = t0 - timedelta(seconds=150)
    assert policy.is_late(t_expired), (
        f"Transaction at T0 - 150s SHOULD be marked late (W = {expected_w0}, Txn = {t_expired})"
    )

    print("[PASS] AT-21: Idle stream watermark non-advancement verified successfully.")


if __name__ == "__main__":
    test_at_21_idle_stream_watermark_non_advancement()
    print("All idle stream tests passed!")
