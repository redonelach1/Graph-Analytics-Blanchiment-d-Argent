"""
validation.py — Deterministic Transaction Validation & Acceptance Logic.

Implements Section 4.2 of project_plan_and_specifications.md:
- VALID: Canonical accepted transaction.
- INVALID: Missing fields, malformed JSON, unsupported schema, invalid amount/timestamp.
- DUPLICATE: Same transaction_id and identical normalized business payload.
- CONFLICT: Same transaction_id with different business payload (original kept, new quarantined).
- SELF_TRANSFER: Source and target account are identical (retained in history, flagged for detector).
- FUTURE_EVENT: Event timestamp exceeds ingestion time by more than configured skew (default 60s).

Provides canonical payload hashing excluding arrival/provenance metadata.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ValidationOutcome(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"
    SELF_TRANSFER = "SELF_TRANSFER"
    FUTURE_EVENT = "FUTURE_EVENT"


# Required fields in input transaction payload
REQUIRED_FIELDS = {
    "schema_version",
    "transaction_id",
    "source_account",
    "target_account",
    "montant",
    "devise",
    "type_operation",
    "timestamp",
}

# ISO-8601 strict timestamp matcher (UTC / with offset)
ISO8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """
    Computes deterministic SHA256 hash of normalized business fields.
    Strictly excludes arrival/provenance metadata (ingest_time, topic, offset, etc.)
    """
    amount = payload.get("montant", payload.get("amount", 0.0))
    normalized_amount = f"{float(amount):.2f}"

    raw_ts = str(payload.get("timestamp", payload.get("event_time", "")))
    try:
        dt = parse_iso_timestamp(raw_ts)
        norm_ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        norm_ts = raw_ts

    business_tuple = (
        str(payload.get("transaction_id", "")).strip(),
        str(payload.get("source_account", payload.get("src", ""))).strip(),
        str(payload.get("target_account", payload.get("dst", ""))).strip(),
        normalized_amount,
        str(payload.get("devise", payload.get("currency", "MAD"))).strip().upper(),
        str(payload.get("type_operation", payload.get("operation_type", ""))).strip(),
        norm_ts,
    )
    raw_str = "|".join(business_tuple)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def parse_iso_timestamp(ts_val: Any) -> datetime:
    """Parses ISO-8601 timestamp string or datetime and converts to UTC datetime."""
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val.astimezone(timezone.utc)
    ts_str = str(ts_val).strip()
    if " " in ts_str and "T" not in ts_str:
        ts_str = ts_str.replace(" ", "T")
    if not ISO8601_PATTERN.match(ts_str):
        raise ValueError(f"Invalid ISO-8601 timestamp format: {ts_str}")

    # Normalize trailing Z to +00:00 for datetime.fromisoformat
    ts_normalized = ts_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts_normalized)
    return dt.astimezone(timezone.utc)


def validate_transaction(
    raw_payload: Any,
    ingest_time: Optional[datetime] = None,
    future_skew_seconds: int = 60,
    supported_currencies: Optional[List[str]] = None,
    existing_hashes_by_id: Optional[Dict[str, str]] = None,
) -> Tuple[ValidationOutcome, List[str], Optional[Dict[str, Any]]]:
    """
    Validates a transaction against all business rules.

    :param raw_payload: Input dict or JSON string.
    :param ingest_time: Ingestion timestamp in UTC (defaults to current UTC time).
    :param future_skew_seconds: Max allowable seconds in the future before rejection.
    :param supported_currencies: List of allowed currencies (default ['MAD']).
    :param existing_hashes_by_id: Lookup map of existing transaction_id -> payload_hash.
    :return: (outcome, reason_codes, normalized_dict_or_None)
    """
    if ingest_time is None:
        ingest_time = datetime.now(timezone.utc)
    if supported_currencies is None:
        supported_currencies = ["MAD"]

    reasons: List[str] = []

    # 1. Parse JSON if string
    if isinstance(raw_payload, str):
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as e:
            return ValidationOutcome.INVALID, [f"MALFORMED_JSON: {e}"], None
    elif isinstance(raw_payload, dict):
        payload = dict(raw_payload)
    else:
        return ValidationOutcome.INVALID, ["PAYLOAD_NOT_OBJECT"], None

    # 2. Check required fields
    missing_fields = REQUIRED_FIELDS - set(payload.keys())
    if missing_fields:
        return ValidationOutcome.INVALID, [f"MISSING_FIELDS: {sorted(list(missing_fields))}"], None

    # 3. Check schema version
    try:
        schema_version = int(payload["schema_version"])
        if schema_version != 1:
            reasons.append(f"UNSUPPORTED_SCHEMA_VERSION: {schema_version}")
    except (ValueError, TypeError):
        reasons.append("INVALID_SCHEMA_VERSION_TYPE")

    # 4. Check non-empty identifiers
    txn_id = str(payload.get("transaction_id", "")).strip()
    src = str(payload.get("source_account", "")).strip()
    dst = str(payload.get("target_account", "")).strip()
    op_type = str(payload.get("type_operation", "")).strip()
    currency = str(payload.get("devise", "")).strip().upper()

    if not txn_id:
        reasons.append("EMPTY_TRANSACTION_ID")
    if not src:
        reasons.append("EMPTY_SOURCE_ACCOUNT")
    if not dst:
        reasons.append("EMPTY_TARGET_ACCOUNT")
    if not op_type:
        reasons.append("EMPTY_OPERATION_TYPE")

    # 5. Check and parse amount (DECIMAL 18,2)
    amount_val = payload.get("montant")
    try:
        # Convert to string to prevent float precision rounding
        dec_amount = Decimal(str(amount_val))
        if dec_amount <= Decimal("0.00"):
            reasons.append("NON_POSITIVE_AMOUNT")
        # Check scale doesn't exceed 2 decimals
        if dec_amount.as_tuple().exponent < -2:
            reasons.append("EXCESS_DECIMAL_PRECISION")
    except (InvalidOperation, TypeError, ValueError):
        reasons.append("INVALID_AMOUNT_FORMAT")
        dec_amount = Decimal("0.00")

    # 6. Check timestamp
    event_time_str = payload.get("timestamp", "")
    event_dt = None
    try:
        event_dt = parse_iso_timestamp(event_time_str)
    except Exception as e:
        reasons.append(f"INVALID_TIMESTAMP: {e}")

    # If any fundamental structure checks failed, classify as INVALID
    if reasons:
        return ValidationOutcome.INVALID, reasons, None

    # 7. Check future event skew
    time_diff = (event_dt - ingest_time).total_seconds()
    if time_diff > future_skew_seconds:
        return (
            ValidationOutcome.FUTURE_EVENT,
            [f"FUTURE_EVENT_SKEW: {time_diff:.1f}s > {future_skew_seconds}s tolerance"],
            None,
        )

    # 8. Check duplicate / conflict against existing state
    current_hash = compute_payload_hash(payload)
    if existing_hashes_by_id and txn_id in existing_hashes_by_id:
        existing_hash = existing_hashes_by_id[txn_id]
        if existing_hash == current_hash:
            return ValidationOutcome.DUPLICATE, ["DUPLICATE_IDENTICAL_PAYLOAD"], None
        else:
            return (
                ValidationOutcome.CONFLICT,
                ["CONFLICT_DIFFERENT_PAYLOAD_FOR_EXISTING_ID"],
                None,
            )

    # 9. Check currency support
    if currency not in supported_currencies:
        reasons.append(f"UNSUPPORTED_CURRENCY: {currency}")

    # 10. Check self-transfer
    is_self_transfer = (src == dst)

    # Build canonical normalized representation
    normalized = {
        "transaction_id": txn_id,
        "src": src,
        "dst": dst,
        "amount": float(dec_amount),
        "currency": currency,
        "operation_type": op_type,
        "event_time": event_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "ingest_time": ingest_time.strftime("%Y-%m-%d %H:%M:%S"),
        "payload_hash": current_hash,
        "online_eligible": not is_self_transfer and (currency in supported_currencies),
        "self_transfer": is_self_transfer,
        "dt": ingest_time.strftime("%Y-%m-%d"),
    }

    if is_self_transfer:
        return ValidationOutcome.SELF_TRANSFER, ["SELF_TRANSFER_EXCLUDED_FROM_TRIANGLES"], normalized

    return ValidationOutcome.VALID, ["OK"], normalized

