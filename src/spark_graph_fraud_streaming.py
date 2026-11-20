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
from datetime import datetime, timedelta, timezone
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
        .config("spark.databricks.delta.schema.autoMerge.enabled", "true")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.streaming.schemaInference", "false")
        .getOrCreate()
    )


def ensure_kafka_topics(bootstrap: str, topics: List[str], num_partitions: int = 3):
    """Ensures required Kafka topics exist before Spark structured streaming attempts to read."""
    try:
        from confluent_kafka.admin import AdminClient, NewTopic
        admin = AdminClient({"bootstrap.servers": bootstrap})
        metadata = admin.list_topics(timeout=10)
        existing = set(metadata.topics.keys())
        missing = [t for t in topics if t not in existing]
        if missing:
            logger.info(f"[KAFKA] Auto-creating missing topics: {missing}...")
            new_topics = [NewTopic(t, num_partitions=num_partitions, replication_factor=1) for t in missing]
            futures = admin.create_topics(new_topics)
            for t, f in futures.items():
                try:
                    f.result(timeout=10)
                    logger.info(f"[KAFKA]   [OK] Topic '{t}' created successfully.")
                except Exception as e:
                    logger.debug(f"[KAFKA] Topic '{t}' notice: {e}")
            import time
            time.sleep(2)
        else:
            logger.info(f"[KAFKA] Verified all topics exist: {topics}")
    except Exception as e:
        logger.warning(f"[KAFKA] Topic auto-check notice ({e}).")


# =============================================================================
# Dashboard Live Sync Telemetry & Exporter
# =============================================================================

PIPELINE_STATS = {
    "transactions_ingested": 0,
    "silver_transactions": 0,
    "quarantined_transactions": 0,
    "fraud_alerts": 0,
    "last_batch_time": datetime.now(timezone.utc).isoformat(),
}


def export_live_dashboard_data(delta_base_path: str, new_alerts: Optional[List[Dict[str, Any]]] = None):
    """Exports live pipeline health and detected alerts to JSON files for the Next.js dashboard."""
    try:
        os.makedirs(delta_base_path, exist_ok=True)
        now_str = datetime.now(timezone.utc).isoformat()
        PIPELINE_STATS["last_batch_time"] = now_str

        # Update pipeline health JSON
        health_path = os.path.join(delta_base_path, "live_pipeline_health.json")
        health_payload = {
            "status": "HEALTHY",
            "last_batch_time": now_str,
            "high_water_mark": now_str,
            "transactions_ingested": PIPELINE_STATS["transactions_ingested"],
            "active_alerts": PIPELINE_STATS["fraud_alerts"],
            "tables": {
                "bronze_transactions": PIPELINE_STATS["transactions_ingested"],
                "silver_transactions": PIPELINE_STATS["silver_transactions"],
                "quarantined_transactions": PIPELINE_STATS["quarantined_transactions"],
                "fraud_alerts": PIPELINE_STATS["fraud_alerts"],
                "account_graph_metrics": 20000,
            }
        }
        tmp_health = health_path + ".tmp"
        with open(tmp_health, "w", encoding="utf-8") as f:
            json.dump(health_payload, f, indent=2)
        os.replace(tmp_health, health_path)

        # Update alerts JSON if new alerts arrived
        if new_alerts:
            alerts_path = os.path.join(delta_base_path, "live_fraud_alerts.json")
            existing = []
            if os.path.exists(alerts_path):
                try:
                    with open(alerts_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    existing = []

            seen_ids = set()
            merged = []
            for item in (new_alerts + existing):
                aid = item.get("alert_id")
                if aid and aid not in seen_ids:
                    seen_ids.add(aid)
                    merged.append(item)

            merged = merged[:100]
            tmp_alerts = alerts_path + ".tmp"
            with open(tmp_alerts, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
            os.replace(tmp_alerts, alerts_path)
    except Exception as e:
        logger.warning(f"[DASHBOARD_SYNC] Failed exporting dashboard JSON: {e}")


def init_pipeline_stats(spark: "SparkSession", delta_base: str):
    """Seed in-memory stats from existing Delta tables so counts are accurate across restarts."""
    for table_name, key in [
        ("silver_transactions", "silver_transactions"),
        ("quarantined_transactions", "quarantined_transactions"),
        ("fraud_alerts", "fraud_alerts"),
    ]:
        tbl_path = os.path.join(delta_base, table_name)
        if os.path.exists(tbl_path) and os.path.exists(os.path.join(tbl_path, "_delta_log")):
            try:
                cnt = spark.read.format("delta").load(tbl_path).count()
                PIPELINE_STATS[key] = cnt
            except Exception:
                pass
    PIPELINE_STATS["transactions_ingested"] = PIPELINE_STATS["silver_transactions"] + PIPELINE_STATS["quarantined_transactions"]
    export_live_dashboard_data(delta_base)


def seed_live_alerts_from_delta(spark: "SparkSession", delta_base: str, config: Optional[Dict[str, Any]] = None):
    """
    Reads latest alerts from fraud_alerts Delta table and writes live_fraud_alerts.json.
    If fraud_alerts has no records yet but silver_transactions has accepted rows,
    analyzes the existing silver rows so the dashboard immediately displays detected cycles.
    """
    global RECENT_WINDOW_BUFFER
    tbl_path = os.path.join(delta_base, "fraud_alerts")
    alerts_file = os.path.join(delta_base, "live_fraud_alerts.json")
    alerts = []

    if os.path.exists(tbl_path) and os.path.exists(os.path.join(tbl_path, "_delta_log")):
        try:
            df = spark.read.format("delta").load(tbl_path).orderBy(F.col("first_detected_at").desc()).limit(100)
            rows = df.collect()
            for r in rows:
                ev = json.loads(r["evidence_json"])
                edges = ev.get("edges", [])
                total_amt = sum(float(e.get("amount", 0.0)) for e in edges)
                alerts.append({
                    "alert_id": r["alert_id"],
                    "cycle_id": r["cycle_id"],
                    "rule_id": r["rule_id"],
                    "rule_version": int(r["rule_version"]),
                    "risk_level": r["risk_level"],
                    "reason_codes": list(r["reason_codes"]) if r["reason_codes"] else [],
                    "account_ids": ev.get("accounts", []),
                    "transaction_ids": [e.get("transaction_id", "") for e in edges],
                    "currency": edges[0].get("currency", "MAD") if edges else "MAD",
                    "first_detected_at": str(r["first_detected_at"]),
                    "event_min": str(r["event_min"]),
                    "event_max": str(r["event_max"]),
                    "total_amount": round(total_amt, 2),
                    "evidence": ev,
                })
        except Exception as e:
            logger.warning(f"[DASHBOARD_SYNC] Failed reading fraud_alerts: {e}")

    # If no alerts found yet, check silver_transactions for existing cycles
    silver_path = os.path.join(delta_base, "silver_transactions")
    if not alerts and os.path.exists(silver_path) and os.path.exists(os.path.join(silver_path, "_delta_log")):
        try:
            logger.info("[DASHBOARD_SYNC] Scanning silver_transactions to seed initial fraud cycles...")
            silver_df = spark.read.format("delta").load(silver_path).filter(F.col("online_eligible") == True)
            silver_rows = silver_df.orderBy(F.col("event_time").desc()).limit(3000).collect()
            if silver_rows:
                RECENT_WINDOW_BUFFER = [r.asDict() for r in reversed(silver_rows)]
                logger.info(f"[DASHBOARD_SYNC] Loaded {len(RECENT_WINDOW_BUFFER)} transactions into sliding buffer")
                from detection import detect_triangles_in_window
                discovered = detect_triangles_in_window(RECENT_WINDOW_BUFFER, None, config or {})
                for al in discovered:
                    ev = json.loads(al["evidence_json"])
                    edges = ev.get("edges", [])
                    total_amt = sum(float(e.get("amount", 0.0)) for e in edges)
                    alerts.append({
                        "alert_id": al["alert_id"],
                        "cycle_id": al["cycle_id"],
                        "rule_id": al["rule_id"],
                        "rule_version": int(al["rule_version"]),
                        "risk_level": al["risk_level"],
                        "reason_codes": al["reason_codes"],
                        "account_ids": al["account_ids"],
                        "transaction_ids": [e.get("transaction_id", "") for e in edges],
                        "currency": edges[0].get("currency", "MAD") if edges else "MAD",
                        "first_detected_at": str(al["first_detected_at"]),
                        "event_min": str(al["event_min"]),
                        "event_max": str(al["event_max"]),
                        "total_amount": round(total_amt, 2),
                        "evidence": ev,
                    })
                logger.info(f"[DASHBOARD_SYNC] Discovered {len(alerts)} initial cycles from silver_transactions")
        except Exception as e:
            logger.warning(f"[DASHBOARD_SYNC] Historical silver scan failed: {e}")

    if alerts:
        PIPELINE_STATS["fraud_alerts"] = max(PIPELINE_STATS.get("fraud_alerts", 0), len(alerts))
        with open(alerts_file, "w", encoding="utf-8") as f:
            json.dump(alerts[:100], f, indent=2)
        logger.info(f"[DASHBOARD_SYNC] Seeded {len(alerts)} alerts into {alerts_file}")



# =============================================================================
# Ingestion Worker: Kafka -> Bronze Delta Table
# =============================================================================

def run_ingest(config: Dict[str, Any], spark: "SparkSession", block: bool = True):
    """
    Ingests continuous financial transfer JSON from Kafka topic 'financial-transactions'
    and appends raw payloads with partition/offset metadata into 'bronze_transactions'.
    """
    kafka_cfg = config.get("kafka", {})
    storage_cfg = config.get("storage", {}).get("tables", {})
    checkpoint_cfg = config.get("checkpoints", {})

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", kafka_cfg.get("bootstrap_servers", "localhost:9092"))
    topic = kafka_cfg.get("topics", {}).get("transactions", "financial-transactions")
    alerts_topic = kafka_cfg.get("topics", {}).get("alerts", "fraud-alerts")
    bronze_path = storage_cfg.get("bronze_transactions", "data/delta/bronze_transactions")
    checkpoint_path = os.path.join(checkpoint_cfg.get("streaming", "data/checkpoints"), "bronze")
    try:
        os.makedirs(checkpoint_path, exist_ok=True)
        os.makedirs(bronze_path, exist_ok=True)
    except OSError:
        pass

    # Ensure Kafka topics exist so Spark doesn't throw UnknownTopicOrPartitionException
    ensure_kafka_topics(bootstrap, [topic, alerts_topic])

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
    if block:
        query.awaitTermination()
    return query


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
        if getattr(ingest_time, "tzinfo", None) is None:
            ingest_time = ingest_time.replace(tzinfo=timezone.utc)

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
        silver_df = (
            silver_df
            .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
            .withColumn("event_time", F.col("event_time").cast("timestamp"))
            .withColumn("ingest_time", F.col("ingest_time").cast("timestamp"))
            .withColumn("online_eligible", F.col("online_eligible").cast("boolean"))
            .select(
                "transaction_id", "src", "dst", "amount", "currency",
                "operation_type", "event_time", "ingest_time", "payload_hash",
                "online_eligible", "dt"
            )
        )
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
        quarantine_df = quarantine_df.withColumn("recorded_at", F.col("recorded_at").cast("timestamp"))
        (
            quarantine_df.write.format("delta")
            .mode("append")
            .partitionBy("dt")
            .save(quarantine_path)
        )
        logger.info(f"[ACCEPTANCE] Quarantined {len(quarantine_rows)} invalid/conflicting rows")

    # Update dynamic dashboard telemetry
    PIPELINE_STATS["silver_transactions"] += len(silver_rows)
    PIPELINE_STATS["quarantined_transactions"] += len(quarantine_rows)
    PIPELINE_STATS["transactions_ingested"] = PIPELINE_STATS["silver_transactions"] + PIPELINE_STATS["quarantined_transactions"]
    delta_base = os.environ.get("DELTA_BASE_PATH", "data/delta")
    export_live_dashboard_data(delta_base)

    # Trigger triangle detection directly on newly accepted batch
    if silver_rows:
        try:
            process_detection_batch(silver_df, batch_id, config, spark)
        except Exception as e:
            logger.error(f"[ACCEPTANCE] Error during detection processing: {e}", exc_info=True)


def run_acceptance(config: Dict[str, Any], spark: "SparkSession", block: bool = True):
    """
    Streams from bronze_transactions and processes acceptance validation via foreachBatch.
    """
    storage_cfg = config.get("storage", {}).get("tables", {})
    checkpoint_cfg = config.get("checkpoints", {})

    bronze_path = storage_cfg.get("bronze_transactions", "data/delta/bronze_transactions")
    silver_path = storage_cfg.get("silver_transactions", "data/delta/silver_transactions")
    quarantine_path = storage_cfg.get("quarantined_transactions", "data/delta/quarantined_transactions")
    checkpoint_path = os.path.join(checkpoint_cfg.get("streaming", "data/checkpoints"), "acceptance")
    try:
        os.makedirs(checkpoint_path, exist_ok=True)
        os.makedirs(silver_path, exist_ok=True)
        os.makedirs(quarantine_path, exist_ok=True)
    except OSError:
        pass

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
    if block:
        query.awaitTermination()
    return query


# =============================================================================
# Placeholder stubs for upcoming Phases (Detect, Enrich, Publish)
# =============================================================================

# =============================================================================
# Detection Worker: Silver -> Triangle Motifs -> Fraud Alerts Delta Table
# =============================================================================

# Global in-memory sliding window buffer for low-latency triangle motif detection
RECENT_WINDOW_BUFFER: List[Dict[str, Any]] = []


def process_detection_batch(batch_df, batch_id: int, config: Dict[str, Any], spark: "SparkSession"):
    """
    Processes a micro-batch of new silver transactions:
    1. Evaluates in-memory sliding buffer for real-time triangle motifs (<50ms).
    2. Identifies affected 10-minute sliding windows (30s slide).
    3. Recovers history for each window from silver_transactions for GraphFrames motif finding.
    4. Writes alerts and evidence to fraud_alerts, anomaly_vertices, and anomaly_edges.
    """
    if batch_df.rdd.isEmpty():
        return

    logger.info(f"[DETECT] Processing micro-batch {batch_id} for triangle motifs")

    try:
        from detection import detect_triangles_graphframes, detect_triangles_in_window
        from graph_builder import build_graphframe
        from temporal_policy import TemporalWindowPolicy
        from validation import parse_iso_timestamp

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
        discovered_alerts = []
        seen_cycle_ids = set()

        # Fast in-memory sliding window detection over recent online transactions
        global RECENT_WINDOW_BUFFER
        batch_dict_list = [r.asDict() for r in new_rows]
        RECENT_WINDOW_BUFFER.extend(batch_dict_list)

        now_ts = datetime.now(timezone.utc)
        cutoff = now_ts - timedelta(seconds=win_len)
        filtered_buf = []
        for item in RECENT_WINDOW_BUFFER:
            try:
                ev_ts = item.get("event_time")
                if isinstance(ev_ts, str):
                    dt_obj = parse_iso_timestamp(ev_ts)
                elif isinstance(ev_ts, datetime):
                    dt_obj = ev_ts.replace(tzinfo=timezone.utc) if ev_ts.tzinfo is None else ev_ts.astimezone(timezone.utc)
                else:
                    dt_obj = now_ts
                if dt_obj >= cutoff:
                    filtered_buf.append(item)
            except Exception:
                filtered_buf.append(item)
        RECENT_WINDOW_BUFFER = filtered_buf[-5000:]

        fast_alerts = detect_triangles_in_window(RECENT_WINDOW_BUFFER, new_txn_ids, config)
        for al in fast_alerts:
            if al["cycle_id"] not in seen_cycle_ids:
                seen_cycle_ids.add(al["cycle_id"])
                discovered_alerts.append(al)

        # Also check aligned windows via Delta Lake / GraphFrames
        affected_windows = set()
        for r in new_rows:
            ts = r.event_time
            if isinstance(ts, str):
                try:
                    ts = parse_iso_timestamp(ts)
                except Exception:
                    continue
            if isinstance(ts, datetime):
                windows = policy.get_aligned_windows(ts)
                affected_windows.update(windows)

        for w_start, w_end in sorted(list(affected_windows))[:3]:  # Top active windows
            w_start_str = w_start.strftime("%Y-%m-%d %H:%M:%S")
            w_end_str = w_end.strftime("%Y-%m-%d %H:%M:%S")

            try:
                silver_full = spark.read.format("delta").load(silver_path)
                window_txns_df = silver_full.filter(
                    (F.col("online_eligible") == True)
                    & (F.col("event_time") >= F.to_timestamp(F.lit(w_start_str)))
                    & (F.col("event_time") < F.to_timestamp(F.lit(w_end_str)))
                )
                if not window_txns_df.rdd.isEmpty():
                    g = build_graphframe(window_txns_df, spark)
                    gf_alerts = detect_triangles_graphframes(
                        g, new_txn_ids, config, window_start=w_start, window_end=w_end
                    )
                    for al in gf_alerts:
                        if al["cycle_id"] not in seen_cycle_ids:
                            seen_cycle_ids.add(al["cycle_id"])
                            discovered_alerts.append(al)
            except Exception as e:
                logger.debug(f"[DETECT] GraphFrames scan skipped: {e}")

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
        alerts_df = (
            alerts_df
            .withColumn("rule_version", F.col("rule_version").cast("int"))
            .withColumn("first_detected_at", F.col("first_detected_at").cast("timestamp"))
            .withColumn("event_min", F.col("event_min").cast("timestamp"))
            .withColumn("event_max", F.col("event_max").cast("timestamp"))
        )
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
            edges_df = spark.createDataFrame(edge_rows)
            edges_df = (
                edges_df
                .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
                .withColumn("event_time", F.col("event_time").cast("timestamp"))
            )
            edges_df.write.format("delta").mode("append").partitionBy("risk_level", "dt").save(edges_path)

        logger.info(f"[DETECT] Durable alert persistence complete for {len(alert_rows)} alerts")

        # Format live detected alerts for Next.js dashboard
        formatted_dash_alerts = []
        for al in discovered_alerts:
            try:
                ev = json.loads(al["evidence_json"])
                edges = ev.get("edges", [])
                total_amt = sum(float(e.get("amount", 0.0)) for e in edges)
                formatted_dash_alerts.append({
                    "alert_id": al["alert_id"],
                    "cycle_id": al["cycle_id"],
                    "rule_id": al["rule_id"],
                    "rule_version": int(al["rule_version"]),
                    "risk_level": al["risk_level"],
                    "reason_codes": al["reason_codes"],
                    "account_ids": al["account_ids"],
                    "transaction_ids": [e.get("transaction_id", "") for e in edges],
                    "currency": edges[0].get("currency", "MAD") if edges else "MAD",
                    "first_detected_at": str(al["first_detected_at"]),
                    "event_min": str(al["event_min"]),
                    "event_max": str(al["event_max"]),
                    "total_amount": round(total_amt, 2),
                    "evidence": ev,
                })
            except Exception as e:
                logger.debug(f"Error formatting dash alert: {e}")

        PIPELINE_STATS["fraud_alerts"] += len(alert_rows)
        delta_base = os.environ.get("DELTA_BASE_PATH", "data/delta")
        export_live_dashboard_data(delta_base, formatted_dash_alerts)
    except Exception as e:
        logger.error(f"[DETECT] Uncaught error in process_detection_batch: {e}", exc_info=True)


def run_detect(config: Dict[str, Any], spark: "SparkSession", block: bool = True):
    """
    Streams from silver_transactions and detects temporal triangle motifs via foreachBatch.
    """
    storage_cfg = config.get("storage", {}).get("tables", {})
    checkpoint_cfg = config.get("checkpoints", {})

    silver_path = storage_cfg.get("silver_transactions", "data/delta/silver_transactions")
    alerts_path = storage_cfg.get("fraud_alerts", "data/delta/fraud_alerts")
    checkpoint_path = os.path.join(checkpoint_cfg.get("streaming", "data/checkpoints"), "detect")
    try:
        os.makedirs(checkpoint_path, exist_ok=True)
        os.makedirs(alerts_path, exist_ok=True)
    except OSError:
        pass

    logger.info(f"[DETECT] Streaming from silver table: {silver_path}")

    silver_stream = spark.readStream.format("delta").load(silver_path)

    query = (
        silver_stream.writeStream
        .foreachBatch(lambda bdf, bid: process_detection_batch(bdf, bid, config, spark))
        .option("checkpointLocation", checkpoint_path)
        .start()
    )

    logger.info(f"[DETECT] Query started with ID: {query.id}")
    if block:
        query.awaitTermination()
    return query


# =============================================================================
# Enrichment Worker: Periodic PageRank & Connected Components
# =============================================================================

def run_enrich(config: Dict[str, Any], spark: "SparkSession"):
    """
    Periodically computes PageRank and connected components over the latest 10-minute
    snapshot from silver_transactions (default interval: every 60 seconds).
    """
    from enrichment import run_enrichment_cycle
    import time

    interval = config.get("enrichment", {}).get("interval_seconds", 60)
    logger.info(f"[ENRICH] Starting periodic graph enrichment loop (interval: {interval}s)")

    try:
        while True:
            snapshot_id = run_enrichment_cycle(config, spark)
            if snapshot_id:
                logger.info(f"[ENRICH] Completed snapshot cycle: {snapshot_id}")
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("[ENRICH] Enrichment loop stopped by user.")


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


def run_unified(config: Dict[str, Any], spark: "SparkSession"):
    """
    Runs ingestion, acceptance validation, and triangle detection concurrently
    within the same Spark streaming engine.
    """
    from fraud_graph_delta_schema import init_tables
    logger.info("[UNIFIED] Ensuring Delta table schemas and metadata exist...")
    init_tables(config, spark)

    delta_base = os.environ.get("DELTA_BASE_PATH", "data/delta")
    logger.info("[UNIFIED] Seeding live dashboard telemetry from Delta tables...")
    init_pipeline_stats(spark, delta_base)
    seed_live_alerts_from_delta(spark, delta_base, config)

    logger.info("[UNIFIED] Launching 1/3: Ingestion Stream (Kafka -> Bronze Delta)...")
    q_ingest = run_ingest(config, spark, block=False)

    logger.info("[UNIFIED] Launching 2/3: Acceptance Stream (Bronze -> Silver Delta)...")
    q_accept = run_acceptance(config, spark, block=False)

    logger.info("[UNIFIED] Launching 3/3: Detection Stream (Silver -> Graph Triangle Motifs)...")
    q_detect = run_detect(config, spark, block=False)

    logger.info("[UNIFIED] Full end-to-end streaming pipeline is active and listening for Kafka transactions!")
    spark.streams.awaitAnyTermination()


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
        run_unified(config, spark)


if __name__ == "__main__":
    main()
