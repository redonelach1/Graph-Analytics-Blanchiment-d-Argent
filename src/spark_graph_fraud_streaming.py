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

# =============================================================================
# Detection Worker: Silver -> Triangle Motifs -> Fraud Alerts Delta Table
# =============================================================================

def process_detection_batch(batch_df, batch_id: int, config: Dict[str, Any], spark: "SparkSession"):
    """
    Processes a micro-batch of new silver transactions:
    1. Identifies affected 10-minute sliding windows (30s slide).
    2. Recovers history for each window from silver_transactions.
    3. Executes GraphFrames motif finding for directed triangles.
    4. Writes alerts and evidence to fraud_alerts, anomaly_vertices, and anomaly_edges.
    """
    if batch_df.rdd.isEmpty():
        return

    logger.info(f"[DETECT] Processing micro-batch {batch_id} for triangle motifs")

    from detection import detect_triangles_graphframes, detect_triangles_in_window
    from graph_builder import build_graphframe
    from temporal_policy import TemporalWindowPolicy

    storage_cfg = config.get("storage", {}).get("tables", {})
    silver_path = storage_cfg.get("silver_transactions", "data/delta/silver_transactions")
    alerts_path = storage_cfg.get("fraud_alerts", "data/delta/fraud_alerts")
    vertices_path = storage_cfg.get("anomaly_vertices", "data/delta/anomaly_vertices")
    edges_path = storage_cfg.get("anomaly_edges", "data/delta/anomaly_edges")

    win_len = config.get("window", {}).get("length_seconds", 600)
    win_slide = config.get("window", {}).get("slide_seconds", 30)
    policy = TemporalWindowPolicy(window_length_seconds=win_len, slide_seconds=win_slide)

    new_rows = batch_df.filter(F.col("online_eligible") == True).collect()
    if not new_rows:
        return

    new_txn_ids = {r.transaction_id for r in new_rows}

    # Find unique affected windows across all new transactions
    affected_windows = set()
    for r in new_rows:
        ts = r.event_time
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        windows = policy.get_aligned_windows(ts)
        affected_windows.update(windows)

    logger.info(f"[DETECT] Batch {batch_id} touches {len(affected_windows)} sliding windows")

    discovered_alerts = []
    seen_cycle_ids = set()

    for w_start, w_end in sorted(list(affected_windows)):
        # Read transactions falling in [w_start, w_end)
        w_start_str = w_start.strftime("%Y-%m-%d %H:%M:%S")
        w_end_str = w_end.strftime("%Y-%m-%d %H:%M:%S")

        silver_full = spark.read.format("delta").load(silver_path)
        window_txns_df = silver_full.filter(
            (F.col("online_eligible") == True)
            & (F.col("event_time") >= w_start_str)
            & (F.col("event_time") < w_end_str)
        )

        if window_txns_df.rdd.isEmpty():
            continue

        try:
            # GraphFrames motif finding
            g = build_graphframe(window_txns_df, spark)
            window_alerts = detect_triangles_graphframes(
                g, new_txn_ids, config, window_start=w_start, window_end=w_end
            )
        except Exception as e:
            # Fallback to pure Python detector on local collects
            logger.debug(f"Using fallback detector for window: {e}")
            window_txns_list = [row.asDict() for row in window_txns_df.collect()]
            window_alerts = detect_triangles_in_window(
                window_txns_list, new_txn_ids, config, window_start=w_start, window_end=w_end
            )

        for al in window_alerts:
            if al["cycle_id"] not in seen_cycle_ids:
                seen_cycle_ids.add(al["cycle_id"])
                discovered_alerts.append(al)

    if not discovered_alerts:
        return

    logger.info(f"[DETECT] Discovered {len(discovered_alerts)} fraud alerts in batch {batch_id}")

    # Build Alert DataFrames and persist to Delta Lake
    alert_rows = []
    vertex_rows = []
    edge_rows = []

    for al in discovered_alerts:
        alert_rows.append({
            "alert_id": al["alert_id"],
            "cycle_id": al["cycle_id"],
            "rule_id": al["rule_id"],
            "rule_version": al["rule_version"],
            "risk_level": al["risk_level"],
            "evidence_json": al["evidence_json"],
            "reason_codes": al["reason_codes"],
            "first_detected_at": al["first_detected_at"],
            "event_min": al["event_min"],
            "event_max": al["event_max"],
            "dt": al["dt"],
        })

        # Anomaly Vertices projection
        for acct in al["account_ids"]:
            vertex_rows.append({
                "alert_id": al["alert_id"],
                "account_id": acct,
                "risk_level": al["risk_level"],
                "dt": al["dt"],
            })

        # Anomaly Edges projection
        evidence = json.loads(al["evidence_json"])
        for edge in evidence.get("edges", []):
            edge_rows.append({
                "alert_id": al["alert_id"],
                "transaction_id": edge["transaction_id"],
                "src": edge["src"],
                "dst": edge["dst"],
                "amount": edge["amount"],
                "currency": edge["currency"],
                "event_time": edge["time"],
                "risk_level": al["risk_level"],
                "dt": al["dt"],
            })

    # Save to fraud_alerts (partitioned by risk_level, dt)
    alerts_df = spark.createDataFrame(alert_rows)
    (
        alerts_df.write.format("delta")
        .mode("append")
        .partitionBy("risk_level", "dt")
        .save(alerts_path)
    )

    # Save projections
    if vertex_rows:
        spark.createDataFrame(vertex_rows).write.format("delta").mode("append").partitionBy("risk_level", "dt").save(vertices_path)
    if edge_rows:
        spark.createDataFrame(edge_rows).write.format("delta").mode("append").partitionBy("risk_level", "dt").save(edges_path)

    logger.info(f"[DETECT] Durable alert persistence complete for {len(alert_rows)} alerts")


def run_detect(config: Dict[str, Any], spark: "SparkSession"):
    """
    Streams from silver_transactions and detects temporal triangle motifs via foreachBatch.
    """
    storage_cfg = config.get("storage", {}).get("tables", {})
    checkpoint_cfg = config.get("checkpoints", {})

    silver_path = storage_cfg.get("silver_transactions", "data/delta/silver_transactions")
    checkpoint_path = os.path.join(checkpoint_cfg.get("streaming", "data/checkpoints"), "detect")

    logger.info(f"[DETECT] Streaming from silver table: {silver_path}")

    silver_stream = spark.readStream.format("delta").load(silver_path)

    query = (
        silver_stream.writeStream
        .foreachBatch(lambda bdf, bid: process_detection_batch(bdf, bid, config, spark))
        .option("checkpointLocation", checkpoint_path)
        .start()
    )

    logger.info(f"[DETECT] Query started with ID: {query.id}")
    query.awaitTermination()


def run_enrich(config: Dict[str, Any], spark: "SparkSession"):
    logger.info("[ENRICH] Periodic graph enrichment worker stub (Implemented in Phase 6)")


# =============================================================================
# Publisher Worker: Unpublished Alerts -> Kafka 'fraud-alerts'
# =============================================================================

def run_publish(config: Dict[str, Any], spark: "SparkSession"):
    """
    Scans fraud_alerts for rows lacking publication progress, publishes them
    to Kafka topic 'fraud-alerts', and records publication progress idempotently.
    """
    from publication import AlertPublisher

    storage_cfg = config.get("storage", {}).get("tables", {})
    alerts_path = storage_cfg.get("fraud_alerts", "data/delta/fraud_alerts")
    progress_path = storage_cfg.get("publication_progress", "data/delta/publication_progress")

    kafka_cfg = config.get("kafka", {})
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", kafka_cfg.get("bootstrap_servers", "localhost:9092"))
    alerts_topic = kafka_cfg.get("topics", {}).get("alerts", "fraud-alerts")

    logger.info(f"[PUBLISH] Monitoring alerts at {alerts_path}")
    logger.info(f"[PUBLISH] Publishing to Kafka topic: {alerts_topic} at {bootstrap}")

    if not os.path.exists(alerts_path):
        logger.warning(f"[PUBLISH] Alerts path {alerts_path} does not exist yet. Exiting.")
        return

    # 1. Load alerts
    alerts_df = spark.read.format("delta").load(alerts_path)
    if alerts_df.rdd.isEmpty():
        logger.info("[PUBLISH] No alerts present in table.")
        return

    # 2. Check already published alert IDs
    published_ids = set()
    if os.path.exists(progress_path):
        try:
            progress_df = spark.read.format("delta").load(progress_path)
            if not progress_df.rdd.isEmpty():
                published_ids = {r.alert_id for r in progress_df.select("alert_id").collect()}
        except Exception as e:
            logger.debug(f"Could not load publication progress: {e}")

    # 3. Filter unpublished alerts
    unpub_df = alerts_df.filter(~F.col("alert_id").isin(list(published_ids))) if published_ids else alerts_df
    unpub_count = unpub_df.count()

    if unpub_count == 0:
        logger.info("[PUBLISH] All alerts have already been published. Nothing to do.")
        return

    logger.info(f"[PUBLISH] Found {unpub_count} unpublished alert(s). Starting publication...")
    publisher = AlertPublisher(bootstrap_servers=bootstrap, topic=alerts_topic)

    progress_records = []
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for row in unpub_df.collect():
        alert_dict = row.asDict()
        success = publisher.publish_alert(alert_dict)
        if success:
            progress_records.append({
                "alert_id": alert_dict["alert_id"],
                "published_at": now_utc,
                "attempt_metadata": f"published_to_{alerts_topic}",
            })

    publisher.flush()

    # 4. Record progress to publication_progress Delta table
    if progress_records:
        prog_df = spark.createDataFrame(progress_records)
        (
            prog_df.write.format("delta")
            .mode("append")
            .save(progress_path)
        )
        logger.info(f"[PUBLISH] Successfully recorded progress for {len(progress_records)} alerts")


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
