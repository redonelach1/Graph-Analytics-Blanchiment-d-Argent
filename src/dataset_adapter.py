"""
dataset_adapter.py — Ingestion Adapter for External AML Datasets.

Transforms external datasets (such as IBM AMLSim) into the standardized
project transaction JSON contract and evaluation truth tables.

Supported AMLSim layouts:
1. 20K_cycle: nodes.csv (nodeid, isFraud, init_balance) + transactions.csv (sourceNodeId, targetNodeId, value, time)
2. smoke: accounts.csv + tx.csv + alerts.csv
"""

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple, Any


class AMLSimAdapter:
    """
    Adapter for converting IBM AMLSim simulation data into canonical transaction events.
    """

    def __init__(
        self,
        dataset_dir: str,
        currency: str = "MAD",
        default_operation_type: str = "VIREMENT_COMMERCIAL",
        base_time: Optional[datetime] = None,
        step_seconds: int = 60,
    ):
        """
        :param dataset_dir: Path to directory containing AMLSim CSVs.
        :param currency: Currency code to assign (default MAD).
        :param default_operation_type: Default operation type string.
        :param base_time: Anchor datetime for step 0 (defaults to 2026-10-07T10:00:00Z).
        :param step_seconds: Duration in seconds represented by 1 simulation step.
        """
        self.dataset_dir = Path(dataset_dir)
        self.currency = currency
        self.default_operation_type = default_operation_type
        self.base_time = base_time or datetime(2026, 10, 7, 10, 0, 0, tzinfo=timezone.utc)
        self.step_seconds = step_seconds

        # Ground truth evaluation mappings (never leaked to detector)
        self.fraud_nodes: Dict[str, bool] = {}
        self.ground_truth_alerts: List[Dict[str, Any]] = []

        self._load_metadata_and_nodes()

    def _load_metadata_and_nodes(self):
        """Loads node fraud labels if available (nodes.csv or accounts.csv)."""
        nodes_csv = self.dataset_dir / "nodes.csv"
        accounts_csv = self.dataset_dir / "accounts.csv"

        if nodes_csv.exists():
            with open(nodes_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    node_id = f"ACC-{row['nodeid'].strip()}"
                    is_fraud = str(row.get("isFraud", "0")).strip().lower() in ("1", "true")
                    self.fraud_nodes[node_id] = is_fraud

        elif accounts_csv.exists():
            with open(accounts_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    acct_id = row.get("ACCOUNT_ID", "").strip()
                    node_id = f"ACC-{acct_id}"
                    is_fraud = str(row.get("isFraud", "false")).strip().lower() in ("1", "true")
                    self.fraud_nodes[node_id] = is_fraud

        # Load alerts.csv if present
        alerts_csv = self.dataset_dir / "alerts.csv"
        if alerts_csv.exists():
            with open(alerts_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.ground_truth_alerts.append(dict(row))

    def _generate_transaction_id(self, source_file: str, ordinal: int) -> str:
        """
        Generates deterministic transaction ID per Section 5 of dataset specifications:
        SHA256(dataset_id + file_id + row_ordinal)
        """
        raw_seed = f"AMLSim:{self.dataset_dir.name}:{source_file}:{ordinal}"
        digest = hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()[:16].upper()
        return f"TXN-AML-{digest}"

    def iter_transactions(
        self,
        time_shift: Optional[timedelta] = None,
        max_rows: Optional[int] = None
    ) -> Iterator[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Yields tuples of:
        (canonical_transaction_payload, evaluation_metadata)

        canonical_transaction_payload contains ONLY valid detector schema fields.
        evaluation_metadata contains ground-truth labels and raw lineage.
        """
        tx_csv = self.dataset_dir / "transactions.csv"
        if not tx_csv.exists():
            tx_csv = self.dataset_dir / "tx.csv"

        if not tx_csv.exists():
            raise FileNotFoundError(f"No transactions CSV found in {self.dataset_dir}")

        row_count = 0

        with open(tx_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in (reader.fieldnames or [])]

            is_20k_format = "sourceNodeId" in headers
            is_smoke_format = "COUNTER_PARTY_ACCOUNT_NUM" in headers

            for ordinal, row in enumerate(reader):
                if max_rows and row_count >= max_rows:
                    break

                if is_20k_format:
                    src_raw = row["sourceNodeId"].strip()
                    dst_raw = row["targetNodeId"].strip()
                    amount = float(row["value"].strip())
                    step = int(row.get("time", 0))
                    op_type = self.default_operation_type
                elif is_smoke_format:
                    src_raw = row["ACCOUNT_ID"].strip()
                    dst_raw = row["COUNTER_PARTY_ACCOUNT_NUM"].strip()
                    amount = float(row.get("TXN_AMOUNT_ORIG", row.get("TXN_AMOUNT", "100.0")).strip())
                    step = int(row.get("start", row.get("TXN_ID", 1)))
                    op_type = row.get("TXN_SOURCE_TYPE_CODE", self.default_operation_type).strip()
                else:
                    # Generic fallback
                    src_raw = row.get("SENDER_ACCOUNT_ID", row.get("src", "0")).strip()
                    dst_raw = row.get("RECEIVER_ACCOUNT_ID", row.get("dst", "1")).strip()
                    amount = float(row.get("AMOUNT", row.get("amount", "100.0")).strip())
                    step = int(row.get("STEP", row.get("step", 0)))
                    op_type = self.default_operation_type

                src_account = f"ACC-{src_raw}"
                dst_account = f"ACC-{dst_raw}"

                # Calculate event timestamp from simulation step
                event_time = self.base_time + timedelta(seconds=step * self.step_seconds)
                if time_shift:
                    event_time += time_shift

                txn_id = self._generate_transaction_id(tx_csv.name, ordinal)

                # Canonical contract (zero label leakage)
                canonical_payload = {
                    "schema_version": 1,
                    "transaction_id": txn_id,
                    "source_account": src_account,
                    "target_account": dst_account,
                    "montant": round(amount, 2),
                    "devise": self.currency,
                    "type_operation": op_type,
                    "timestamp": event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }

                # Separate evaluation metadata
                eval_meta = {
                    "raw_ordinal": ordinal,
                    "simulation_step": step,
                    "source_file": tx_csv.name,
                    "src_is_fraud": self.fraud_nodes.get(src_account, False),
                    "dst_is_fraud": self.fraud_nodes.get(dst_account, False),
                }

                row_count += 1
                yield canonical_payload, eval_meta

    def export_canonical_jsonl(self, output_path: str, max_rows: Optional[int] = None) -> int:
        """Exports canonical transactions to a JSON Lines file."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(out, "w", encoding="utf-8") as f:
            for payload, _ in self.iter_transactions(max_rows=max_rows):
                f.write(json.dumps(payload) + "\n")
                count += 1
        return count

