#!/usr/bin/env python3
"""
financial_graph_producer.py — Synthetic & AMLSim Transaction Producer

Entry point 1/4 of Mini-Projet 17.
Generates financial transactions and publishes to the Kafka topic
'financial-transactions' (or dry-run to stdout / file).

Modes:
  --mode normal    : Benign random transactions
  --mode triangle  : Guaranteed 3-account cycles within a 10-minute window
  --mode mixed     : 90% normal traffic + 10% injected triangles
  --mode replay    : Replay a local JSON fixture
  --mode amlsim    : Stream records from IBM AMLSim dataset
"""

import argparse
import hashlib
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Attempt importing confluent_kafka (falls back gracefully in local test / dry-run mode)
try:
    from confluent_kafka import Producer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from config_loader import load_config
from dataset_adapter import AMLSimAdapter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("financial_graph_producer")


class TransactionGenerator:
    """Generates synthetic transactions with controllable seeds and topology."""

    def __init__(self, config: Dict[str, Any], seed: int = 42):
        self.rng = random.Random(seed)
        self.config = config
        prod_cfg = config.get("producer", {})
        self.num_accounts = prod_cfg.get("num_accounts", 100)
        self.accounts = [f"ACC-{i:04d}" for i in range(self.num_accounts)]
        self.amount_min = prod_cfg.get("amount_range", {}).get("min", 100.0)
        self.amount_max = prod_cfg.get("amount_range", {}).get("max", 500000.0)
        self.op_types = prod_cfg.get("operation_types", [
            "VIREMENT_COMMERCIAL", "VIREMENT_PERSONNEL", "PAIEMENT_FACTURE"
        ])
        self.currencies = config.get("detection", {}).get("supported_currencies", ["MAD"])
        self.default_currency = self.currencies[0] if self.currencies else "MAD"

    def _make_txn(
        self,
        src: str,
        dst: str,
        amount: Optional[float] = None,
        event_time: Optional[datetime] = None,
        currency: Optional[str] = None,
        op_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a single canonical transaction payload."""
        if event_time is None:
            event_time = datetime.now(timezone.utc)
        if amount is None:
            amount = round(self.rng.uniform(self.amount_min, self.amount_max), 2)
        if currency is None:
            currency = self.default_currency
        if op_type is None:
            op_type = self.rng.choice(self.op_types)

        # Deterministic transaction ID
        ts_str = event_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        id_seed = f"{src}->{dst}:{amount}:{currency}:{ts_str}:{self.rng.random()}"
        txn_id = f"TXN-{hashlib.sha256(id_seed.encode()).hexdigest()[:12].upper()}"

        return {
            "schema_version": 1,
            "transaction_id": txn_id,
            "source_account": src,
            "target_account": dst,
            "montant": round(amount, 2),
            "devise": currency,
            "type_operation": op_type,
            "timestamp": ts_str,
        }

    def generate_normal(self, event_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Generates a benign transaction between distinct accounts."""
        src, dst = self.rng.sample(self.accounts, 2)
        return self._make_txn(src, dst, event_time=event_time)

    def generate_triangle(self, base_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Generates 3 transactions forming a directed cycle A -> B -> C -> A
        strictly within a 10-minute window (e.g. within 60-300 seconds).
        """
        if base_time is None:
            base_time = datetime.now(timezone.utc)

        a, b, c = self.rng.sample(self.accounts, 3)
        # Choose amount with slight fee slippage (e.g., 50000 -> 49000 -> 48000)
        base_amt = round(self.rng.uniform(50000.0, 200000.0), 2)
        amt1 = base_amt
        amt2 = round(base_amt * self.rng.uniform(0.95, 0.99), 2)
        amt3 = round(amt2 * self.rng.uniform(0.95, 0.99), 2)

        t1 = base_time
        t2 = base_time + timedelta(seconds=self.rng.randint(30, 180))
        t3 = t2 + timedelta(seconds=self.rng.randint(30, 240))

        return [
            self._make_txn(a, b, amount=amt1, event_time=t1),
            self._make_txn(b, c, amount=amt2, event_time=t2),
            self._make_txn(c, a, amount=amt3, event_time=t3),
        ]


class KafkaSink:
    """Handles Kafka publication with callbacks and flushing."""

    def __init__(self, bootstrap_servers: str, topic: str):
        if not KAFKA_AVAILABLE:
            raise RuntimeError(
                "confluent-kafka library is not installed. Use --dry-run or pip install confluent-kafka"
            )
        self.topic = topic
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "acks": "all",
            "linger.ms": 10,
            "retries": 3,
        })
        self.delivered_count = 0
        self.error_count = 0

    def _delivery_callback(self, err, msg):
        if err:
            self.error_count += 1
            logger.error(f"Kafka delivery failed: {err}")
        else:
            self.delivered_count += 1

    def send(self, payload: Dict[str, Any]):
        key = payload["source_account"].encode("utf-8")
        value = json.dumps(payload).encode("utf-8")
        self.producer.produce(
            topic=self.topic,
            key=key,
            value=value,
            on_delivery=self._delivery_callback
        )
        self.producer.poll(0)

    def flush(self):
        self.producer.flush()
        logger.info(
            f"Kafka flush complete: {self.delivered_count} delivered, "
            f"{self.error_count} errors"
        )


def main():
    parser = argparse.ArgumentParser(description="Financial Graph Producer (Mini-Projet 17)")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config")
    parser.add_argument(
        "--mode",
        choices=["normal", "triangle", "mixed", "replay", "amlsim"],
        default="normal",
        help="Generation / replay mode"
    )
    parser.add_argument("--rate", "--tps", dest="rate", type=float, default=None, help="Transactions per second (rate limit)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatability")
    parser.add_argument("--count", type=int, default=1000, help="Total transactions to emit (0 for infinite)")
    parser.add_argument("--fixture", type=str, default=None, help="Path to fixture JSON (for replay mode)")
    parser.add_argument(
        "--amlsim-dir",
        type=str,
        default="data/datasets/amlsim/20K_cycle/20K_cycle200",
        help="Path to AMLSim dataset dir"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print / log events without publishing to Kafka")
    parser.add_argument("--output", type=str, default=None, help="Save emitted records to JSONL file")

    args = parser.parse_args()

    config = load_config(args.config)
    rate = args.rate if args.rate is not None else config.get("producer", {}).get("default_rate", 10)
    delay = 1.0 / rate if rate > 0 else 0.0

    logger.info(f"Starting Producer in mode='{args.mode}', rate={rate}/s, seed={args.seed}")

    sink = None
    if not args.dry_run:
        bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", config.get("kafka", {}).get("bootstrap_servers", "kafka:9094"))
        topic = config.get("kafka", {}).get("topics", {}).get("transactions", "financial-transactions")
        try:
            sink = KafkaSink(bootstrap, topic)
            logger.info(f"Connected to Kafka at {bootstrap}, topic: {topic}")
        except Exception as e:
            logger.warning(f"Could not connect to Kafka ({e}). Falling back to dry-run mode.")
            args.dry_run = True

    out_file = None
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_file = open(out_path, "w", encoding="utf-8")

    generator = TransactionGenerator(config, seed=args.seed)
    emitted = 0

    try:
        if args.mode == "replay":
            if not args.fixture:
                logger.error("--fixture argument required for replay mode")
                sys.exit(1)
            with open(args.fixture, "r", encoding="utf-8") as f:
                data = json.load(f)
            txns = data.get("transactions", data if isinstance(data, list) else [])
            for txn in txns:
                _emit_record(txn, sink, out_file, args.dry_run)
                emitted += 1
                if delay > 0:
                    time.sleep(delay)

        elif args.mode == "amlsim":
            adapter = AMLSimAdapter(args.amlsim_dir)
            logger.info(f"Streaming from AMLSim directory: {args.amlsim_dir}")
            for txn, meta in adapter.iter_transactions(max_rows=args.count):
                _emit_record(txn, sink, out_file, args.dry_run)
                emitted += 1
                if delay > 0:
                    time.sleep(delay)

        elif args.mode == "triangle":
            while args.count <= 0 or emitted < args.count:
                cycle_txns = generator.generate_triangle()
                for txn in cycle_txns:
                    _emit_record(txn, sink, out_file, args.dry_run)
                    emitted += 1
                    if delay > 0:
                        time.sleep(delay)

        elif args.mode == "mixed":
            while args.count <= 0 or emitted < args.count:
                # 90% normal, 10% triangle
                if random.random() < 0.10 and (args.count <= 0 or emitted + 3 <= args.count):
                    cycle_txns = generator.generate_triangle()
                    for txn in cycle_txns:
                        _emit_record(txn, sink, out_file, args.dry_run)
                        emitted += 1
                        if delay > 0:
                            time.sleep(delay)
                else:
                    txn = generator.generate_normal()
                    _emit_record(txn, sink, out_file, args.dry_run)
                    emitted += 1
                    if delay > 0:
                        time.sleep(delay)

        else:  # normal
            while args.count <= 0 or emitted < args.count:
                txn = generator.generate_normal()
                _emit_record(txn, sink, out_file, args.dry_run)
                emitted += 1
                if delay > 0:
                    time.sleep(delay)

    finally:
        if sink:
            sink.flush()
        if out_file:
            out_file.close()

    logger.info(f"Producer finished. Total records emitted: {emitted}")


def _emit_record(txn: Dict[str, Any], sink: Optional[KafkaSink], out_file, dry_run: bool):
    if sink:
        sink.send(txn)
    if out_file:
        out_file.write(json.dumps(txn) + "\n")
    if dry_run:
        print(f"[EMIT] {txn['transaction_id']} | {txn['source_account']} -> {txn['target_account']} | {txn['montant']} {txn['devise']} | {txn['timestamp']}")


if __name__ == "__main__":
    main()
