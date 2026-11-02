#!/usr/bin/env python3
"""
spark_graph_fraud_streaming.py — Spark Structured Streaming Pipeline.

Entry point 3/4 of Mini-Projet 17.
Orchestrates streaming ingestion, acceptance, graph detection, enrichment, and publication.

Roles:
  --role ingest   : Streams from Kafka into bronze_transactions
  --role accept   : Validates bronze records into silver and quarantine Delta tables
  --role detect   : Temporal triangle motif detection over sliding windows
  --role enrich   : Periodic PageRank and connected components
  --role publish  : Publishes detected alerts to Kafka 'fraud-alerts'
  --role all      : Runs all roles concurrently / in unified pipeline

Usage:
  spark-submit spark_graph_fraud_streaming.py --config config/default.yaml --role ingest
  python spark_graph_fraud_streaming.py --config config/default.yaml --role accept
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config_loader import load_config
from validation import ValidationOutcome, validate_transaction

try:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.types import StringType
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("spark_graph_fraud_streaming")


def get_spark_session(app_name: str = "AML-GraphFraudStreaming") -> "SparkSession":
    """Initializes or returns an active Spark session with Delta extensions."""
    if not PYSPARK_AVAILABLE:
        raise RuntimeError("PySpark is required to run the streaming pipeline.")

    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.streaming.schemaInference", "false")
        .getOrCreate()
    )


# =============================================================================
# Ingestion Worker: Kafka -> Bronze Delta Table
# =============================================================================

def run_ingest(config: Dict[str, Any], spark: "SparkSession"):
    """
    Ingests continuous financial transfer JSON from Kafka topic 'financial-transactions'
    and appends raw payloads with partition/offset metadata into 'bronze_transactions'.
    """
    kafka_cfg = config.get("kafka", {})
    storage_cfg = config.get("storage", {}).get("tables", {})
    checkpoint_cfg = config.get("checkpoints", {})

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", kafka_cfg.get("bootstrap_servers", "localhost:9092"))
    topic = kafka_cfg.get("topics", {}).get("transactions", "financial-transactions")
    bronze_path = storage_cfg.get("bronze_transactions", "data/delta/bronze_transactions")
    checkpoint_path = os.path.join(checkpoint_cfg.get("streaming", "data/checkpoints"), "bronze")

    logger.info(f"[INGEST] Starting Kafka source: {bootstrap}, topic: {topic}")
    logger.info(f"[INGEST] Target Delta table: {bronze_path}")

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "earliest")
        .load()
    )

    bronze_df = raw_stream.select(
        F.col("value").cast("string").alias("raw_json"),
        F.col("topic"),
        F.col("partition"),
        F.col("offset"),
        F.current_timestamp().alias("ingest_time"),
        F.date_format(F.current_timestamp(), "yyyy-MM-dd").alias("dt"),
    )

    query = (
        bronze_df.writeStream.format("delta")
        .outputMode("append")
        .partitionBy("dt")
        .option("checkpointLocation", checkpoint_path)
        .start(bronze_path)
    )

    logger.info(f"[INGEST] Query started with ID: {query.id}")
    query.awaitTermination()


# =============================================================================
# Acceptance Worker: Bronze -> Silver / Quarantine Delta Tables
# =============================================================================

def process_acceptance_batch(batch_df, batch_id: int, config: Dict[str, Any], spark: "SparkSession"):
    """
    Processes a micro-batch of raw bronze records, applying deterministic validation.
    Routes to silver_transactions or quarantined_transactions.
    """
    if batch_df.rdd.isEmpty():
        return

    logger.info(f"[ACCEPTANCE] Processing micro-batch {batch_id} ({batch_df.count()} records)")

    storage_cfg = config.get("storage", {}).get("tables", {})
    silver_path = storage_cfg.get("silver_transactions", "data/delta/silver_transactions")
    quarantine_path = storage_cfg.get("quarantined_transactions", "data/delta/quarantined_transactions")
    skew_tol = config.get("lateness", {}).get("future_skew_tolerance_seconds", 60)
    supported_currs = config.get("detection", {}).get("supported_currencies", ["MAD"])

    # Load existing transaction hashes to detect duplicate/conflict
    existing_hashes = {}
    try:
        if os.path.exists(silver_path):
            existing_silver = spark.read.format("delta").load(silver_path)
            rows = existing_silver.select("transaction_id", "payload_hash").collect()
            existing_hashes = {r.transaction_id: r.payload_hash for r in rows}
    except Exception as e:
        logger.debug(f"No previous silver state loaded: {e}")

    silver_rows = []
    quarantine_rows = []

    # Validate each raw record deterministically
    records = batch_df.select("raw_json", "topic", "partition", "offset", "ingest_time").collect()
    now_utc = datetime.now(timezone.utc)

    for rec in records:
        ingest_time = rec.ingest_time if rec.ingest_time else now_utc
        if isinstance(ingest_time, str):
            ingest_time = datetime.fromisoformat(ingest_time.replace("Z", "+00:00"))

        outcome, reasons, normalized = validate_transaction(
            raw_payload=rec.raw_json,
            ingest_time=ingest_time,
            future_skew_seconds=skew_tol,
            supported_currencies=supported_currs,
            existing_hashes_by_id=existing_hashes,
        )

        source_id = f"{rec.topic}:{rec.partition}:{rec.offset}"

        if outcome in (ValidationOutcome.VALID, ValidationOutcome.SELF_TRANSFER):
            silver_rows.append(normalized)
            # Update local map so subsequent occurrences in same micro-batch are caught as duplicates
            existing_hashes[normalized["transaction_id"]] = normalized["payload_hash"]

        elif outcome in (ValidationOutcome.INVALID, ValidationOutcome.CONFLICT, ValidationOutcome.FUTURE_EVENT):
            quarantine_rows.append({
                "source_identity": source_id,
                "raw_json": str(rec.raw_json),
                "reason_codes": reasons,
                "recorded_at": ingest_time.strftime("%Y-%m-%d %H:%M:%S"),
                "dt": ingest_time.strftime("%Y-%m-%d"),
            })
        elif outcome == ValidationOutcome.DUPLICATE:
            # Idempotently ignored
            logger.debug(f"Duplicate transaction ignored: {rec.raw_json}")

    # Write to Silver Delta Table
    if silver_rows:
        silver_df = spark.createDataFrame(silver_rows)
        (
            silver_df.write.format("delta")
            .mode("append")
            .partitionBy("dt")
            .save(silver_path)
        )
        logger.info(f"[ACCEPTANCE] Appended {len(silver_rows)} accepted rows to silver_transactions")

    # Write to Quarantine Delta Table
    if quarantine_rows:
        quarantine_df = spark.createDataFrame(quarantine_rows)
        (
            quarantine_df.write.format("delta")
            .mode("append")
            .partitionBy("dt")
            .save(quarantine_path)
        )
        logger.info(f"[ACCEPTANCE] Quarantined {len(quarantine_rows)} invalid/conflicting rows")


def run_acceptance(config: Dict[str, Any], spark: "SparkSession"):
    """
    Streams from bronze_transactions and processes acceptance validation via foreachBatch.
    """
    storage_cfg = config.get("storage", {}).get("tables", {})
    checkpoint_cfg = config.get("checkpoints", {})

    bronze_path = storage_cfg.get("bronze_transactions", "data/delta/bronze_transactions")
    checkpoint_path = os.path.join(checkpoint_cfg.get("streaming", "data/checkpoints"), "acceptance")

    logger.info(f"[ACCEPTANCE] Streaming from bronze table: {bronze_path}")

    bronze_stream = (
        spark.readStream.format("delta")
        .load(bronze_path)
    )

    query = (
        bronze_stream.writeStream
        .foreachBatch(lambda bdf, bid: process_acceptance_batch(bdf, bid, config, spark))
        .option("checkpointLocation", checkpoint_path)
        .start()
    )

    logger.info(f"[ACCEPTANCE] Query started with ID: {query.id}")
    query.awaitTermination()


# =============================================================================
# Placeholder stubs for upcoming Phases (Detect, Enrich, Publish)
# =============================================================================

def run_detect(config: Dict[str, Any], spark: "SparkSession"):
    logger.info("[DETECT] Detection worker stub (Implemented in Phase 4)")


def run_enrich(config: Dict[str, Any], spark: "SparkSession"):
    logger.info("[ENRICH] Periodic graph enrichment worker stub (Implemented in Phase 6)")


def run_publish(config: Dict[str, Any], spark: "SparkSession"):
    logger.info("[PUBLISH] Kafka alert publisher worker stub (Implemented in Phase 5)")


def main():
    parser = argparse.ArgumentParser(description="Spark Graph Fraud Streaming Pipeline")
    parser.add_argument("--config", default="config/default.yaml", help="Path to config YAML")
    parser.add_argument(
        "--role",
        choices=["ingest", "accept", "detect", "enrich", "publish", "all"],
        default="all",
        help="Pipeline role to run",
    )
    args = parser.parse_args()
    config = load_config(args.config)

    logger.info(f"Starting spark_graph_fraud_streaming.py with role='{args.role}'")

    if not PYSPARK_AVAILABLE:
        logger.warning("PySpark is not installed in the current environment. To run streaming queries, use Spark container.")
        sys.exit(0)

    spark = get_spark_session()

    if args.role == "ingest":
        run_ingest(config, spark)
    elif args.role == "accept":
        run_acceptance(config, spark)
    elif args.role == "detect":
        run_detect(config, spark)
    elif args.role == "enrich":
        run_enrich(config, spark)
    elif args.role == "publish":
        run_publish(config, spark)
    elif args.role == "all":
        # In single-process demo mode, run ingestion/acceptance
        logger.info("Running unified pipeline...")
        run_ingest(config, spark)


if __name__ == "__main__":
    main()
