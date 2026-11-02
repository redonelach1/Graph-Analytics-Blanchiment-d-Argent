"""
test_dataset_adapter.py — Verification of Dataset Adapter & Contract Conformance.

Verifies acceptance criteria:
- DS-AT-01: Repeat adaptation produces identical transaction IDs
- DS-AT-02: Repeated equal-content transfers remain distinct transactions
- DS-AT-04: Shifted-time replay preserves pairwise delta times
- DS-AT-06: Fraud labels are absent from detector canonical payload
- DS-AT-09: Handles small smoke test dataset cleanly
"""

import sys
from datetime import timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dataset_adapter import AMLSimAdapter


def test_repeat_adaptation_identical_ids():
    """DS-AT-01: Repeat adaptation produces identical transaction IDs."""
    adapter1 = AMLSimAdapter("data/datasets/amlsim/smoke")
    adapter2 = AMLSimAdapter("data/datasets/amlsim/smoke")

    txns1 = [t["transaction_id"] for t, _ in adapter1.iter_transactions(max_rows=10)]
    txns2 = [t["transaction_id"] for t, _ in adapter2.iter_transactions(max_rows=10)]

    assert txns1 == txns2, "Transaction IDs must be deterministic and identical across repeated runs"
    print("[PASS] DS-AT-01: Repeat adaptation produces identical transaction IDs")


def test_repeated_equal_content_distinct_ids():
    """DS-AT-02: Repeated equal-content transfers receive distinct IDs."""
    adapter = AMLSimAdapter("data/datasets/amlsim/20K_cycle/20K_cycle200")
    txns = [t["transaction_id"] for t, _ in adapter.iter_transactions(max_rows=50)]
    # All transaction IDs must be unique
    assert len(txns) == len(set(txns)), "Distinct source records must receive distinct transaction IDs"
    print("[PASS] DS-AT-02: Distinct source records receive distinct transaction IDs")


def test_shifted_time_preserves_deltas():
    """DS-AT-04: Shifted-time replay preserves pairwise time differences."""
    from datetime import datetime

    adapter1 = AMLSimAdapter("data/datasets/amlsim/smoke")
    adapter2 = AMLSimAdapter("data/datasets/amlsim/smoke")

    shift = timedelta(days=365, hours=2)
    txns_orig = [t["timestamp"] for t, _ in adapter1.iter_transactions(max_rows=5)]
    txns_shift = [t["timestamp"] for t, _ in adapter2.iter_transactions(time_shift=shift, max_rows=5)]

    for t_orig, t_shift in zip(txns_orig, txns_shift):
        dt_orig = datetime.fromisoformat(t_orig.replace("Z", "+00:00"))
        dt_shift = datetime.fromisoformat(t_shift.replace("Z", "+00:00"))
        diff = dt_shift - dt_orig
        assert diff == shift, f"Expected shift {shift}, got {diff}"

    print("[PASS] DS-AT-04: Shifted-time replay preserves pairwise delta times")


def test_labels_absent_from_canonical_payload():
    """DS-AT-06: Fraud labels are absent from detector canonical payload."""
    adapter = AMLSimAdapter("data/datasets/amlsim/20K_cycle/20K_cycle200")
    forbidden_keys = {"isFraud", "fraud", "is_fraud", "label", "alert", "fraudStep"}

    for payload, meta in adapter.iter_transactions(max_rows=20):
        # Payload must only contain valid detector contract fields
        keys = set(payload.keys())
        leakage = keys.intersection(forbidden_keys)
        assert not leakage, f"Detector payload contains leaked label keys: {leakage}"

        # Schema must match expected contract
        assert "schema_version" in payload
        assert "transaction_id" in payload
        assert "source_account" in payload
        assert "target_account" in payload
        assert "montant" in payload
        assert "devise" in payload
        assert "type_operation" in payload
        assert "timestamp" in payload

    print("[PASS] DS-AT-06: Fraud labels are strictly absent from detector canonical payload")


def test_smoke_dataset_handling():
    """DS-AT-09: Handles small smoke test dataset cleanly."""
    adapter = AMLSimAdapter("data/datasets/amlsim/smoke")
    txns = list(adapter.iter_transactions())
    assert len(txns) > 0, "Smoke dataset should yield transactions"
    print(f"[PASS] DS-AT-09: Smoke dataset loaded {len(txns)} records successfully")


if __name__ == "__main__":
    test_repeat_adaptation_identical_ids()
    test_repeated_equal_content_distinct_ids()
    test_shifted_time_preserves_deltas()
    test_labels_absent_from_canonical_payload()
    test_smoke_dataset_handling()
    print("\nALL DATASET ADAPTER ACCEPTANCE TESTS PASSED!")
