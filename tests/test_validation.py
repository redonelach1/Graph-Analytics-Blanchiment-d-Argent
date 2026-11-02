"""
test_validation.py — Unit Tests for Transaction Validation & Acceptance Logic.

Tests:
1. Valid canonical transactions -> outcome VALID, online_eligible True
2. Missing required fields -> outcome INVALID
3. Malformed JSON string -> outcome INVALID
4. Non-positive amount & excess decimal precision -> outcome INVALID
5. Self-transfer (src == dst) -> outcome SELF_TRANSFER, online_eligible False
6. Future event skew exceeding tolerance (>60s) -> outcome FUTURE_EVENT
7. Duplicate transaction (identical payload) -> outcome DUPLICATE
8. Conflicting transaction (same ID, different content) -> outcome CONFLICT
9. Payload hash consistency and isolation from arrival metadata
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validation import (
    ValidationOutcome,
    compute_payload_hash,
    validate_transaction,
)


def make_valid_payload():
    return {
        "schema_version": 1,
        "transaction_id": "TXN-TEST-1001",
        "source_account": "ACC-0001",
        "target_account": "ACC-0002",
        "montant": 25000.50,
        "devise": "MAD",
        "type_operation": "VIREMENT_COMMERCIAL",
        "timestamp": "2026-10-07T10:00:00Z",
    }


def test_valid_transaction():
    payload = make_valid_payload()
    ingest_time = datetime(2026, 10, 7, 10, 0, 10, tzinfo=timezone.utc)
    outcome, reasons, normalized = validate_transaction(payload, ingest_time=ingest_time)

    assert outcome == ValidationOutcome.VALID, f"Expected VALID, got {outcome}"
    assert reasons == ["OK"]
    assert normalized is not None
    assert normalized["transaction_id"] == "TXN-TEST-1001"
    assert normalized["src"] == "ACC-0001"
    assert normalized["dst"] == "ACC-0002"
    assert normalized["amount"] == 25000.50
    assert normalized["online_eligible"] is True
    assert normalized["self_transfer"] is False
    print("[PASS] test_valid_transaction: Normal valid transaction accepted")


def test_missing_fields_invalid():
    payload = make_valid_payload()
    del payload["source_account"]
    outcome, reasons, norm = validate_transaction(payload)

    assert outcome == ValidationOutcome.INVALID
    assert any("MISSING_FIELDS" in r for r in reasons)
    print("[PASS] test_missing_fields_invalid: Missing fields correctly flagged as INVALID")


def test_malformed_json_invalid():
    outcome, reasons, norm = validate_transaction("{not a valid json")
    assert outcome == ValidationOutcome.INVALID
    assert any("MALFORMED_JSON" in r for r in reasons)
    print("[PASS] test_malformed_json_invalid: Malformed JSON flagged as INVALID")


def test_non_positive_amount_and_excess_precision():
    # Negative amount
    p_neg = make_valid_payload()
    p_neg["montant"] = -50.0
    outcome, reasons, _ = validate_transaction(p_neg)
    assert outcome == ValidationOutcome.INVALID
    assert "NON_POSITIVE_AMOUNT" in reasons

    # Zero amount
    p_zero = make_valid_payload()
    p_zero["montant"] = 0.0
    outcome, reasons, _ = validate_transaction(p_zero)
    assert outcome == ValidationOutcome.INVALID
    assert "NON_POSITIVE_AMOUNT" in reasons

    # Excess decimal precision (3 decimal places)
    p_prec = make_valid_payload()
    p_prec["montant"] = 12.345
    outcome, reasons, _ = validate_transaction(p_prec)
    assert outcome == ValidationOutcome.INVALID
    assert "EXCESS_DECIMAL_PRECISION" in reasons
    print("[PASS] test_non_positive_amount_and_excess_precision: Invalid amounts rejected")


def test_self_transfer():
    payload = make_valid_payload()
    payload["target_account"] = payload["source_account"]  # ACC-0001 -> ACC-0001
    outcome, reasons, norm = validate_transaction(payload)

    assert outcome == ValidationOutcome.SELF_TRANSFER
    assert norm["self_transfer"] is True
    assert norm["online_eligible"] is False
    print("[PASS] test_self_transfer: Self transfer identified and excluded from online triangles")


def test_future_event_skew():
    payload = make_valid_payload()
    # Event is 120s in future relative to ingest_time
    ingest_time = datetime(2026, 10, 7, 9, 58, 0, tzinfo=timezone.utc)
    outcome, reasons, norm = validate_transaction(
        payload, ingest_time=ingest_time, future_skew_seconds=60
    )

    assert outcome == ValidationOutcome.FUTURE_EVENT
    assert any("FUTURE_EVENT_SKEW" in r for r in reasons)
    print("[PASS] test_future_event_skew: Excessive future skew quarantined")


def test_duplicate_and_conflict():
    payload1 = make_valid_payload()
    hash1 = compute_payload_hash(payload1)
    existing_hashes = {payload1["transaction_id"]: hash1}

    # Same payload -> DUPLICATE
    outcome, reasons, norm = validate_transaction(
        payload1, existing_hashes_by_id=existing_hashes
    )
    assert outcome == ValidationOutcome.DUPLICATE
    assert "DUPLICATE_IDENTICAL_PAYLOAD" in reasons

    # Different payload with same transaction_id -> CONFLICT
    payload_conflict = make_valid_payload()
    payload_conflict["montant"] = 99999.00
    outcome, reasons, norm = validate_transaction(
        payload_conflict, existing_hashes_by_id=existing_hashes
    )
    assert outcome == ValidationOutcome.CONFLICT
    assert "CONFLICT_DIFFERENT_PAYLOAD_FOR_EXISTING_ID" in reasons
    print("[PASS] test_duplicate_and_conflict: DUPLICATE and CONFLICT outcomes correctly distinguished")


def test_payload_hash_properties():
    p1 = make_valid_payload()
    h1 = compute_payload_hash(p1)

    # Identical business data produces identical hash
    p2 = make_valid_payload()
    h2 = compute_payload_hash(p2)
    assert h1 == h2

    # Modified business data alters hash
    p3 = make_valid_payload()
    p3["montant"] = 25000.51
    h3 = compute_payload_hash(p3)
    assert h1 != h3
    print("[PASS] test_payload_hash_properties: Payload hash is deterministic and sensitive to business fields")


if __name__ == "__main__":
    test_valid_transaction()
    test_missing_fields_invalid()
    test_malformed_json_invalid()
    test_non_positive_amount_and_excess_precision()
    test_self_transfer()
    test_future_event_skew()
    test_duplicate_and_conflict()
    test_payload_hash_properties()
    print("\nALL TRANSACTION VALIDATION TESTS PASSED!")

