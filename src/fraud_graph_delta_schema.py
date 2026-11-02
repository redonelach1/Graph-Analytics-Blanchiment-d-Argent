#!/usr/bin/env python3
"""
fraud_graph_delta_schema.py — Delta Lake Schema Definitions & Table Initializer.

Entry point 2/4 of Mini-Projet 17.
Defines schemas and partition strategies for all 10 Delta Lake tables per Section 8
of project_plan_and_specifications.md:

1. bronze_transactions       (partitioned by dt)
2. silver_transactions       (partitioned by dt)
3. quarantined_transactions  (partitioned by dt)
4. fraud_alerts              (partitioned by risk_level, dt)
5. anomaly_vertices          (partitioned by risk_level, dt)
6. anomaly_edges             (partitioned by risk_level, dt)
7. graph_snapshots           (partitioned by dt)
8. account_graph_metrics     (partitioned by dt)
9. processing_progress       (unpartitioned)
10. publication_progress     (unpartitioned)

Usage:
  python fraud_graph_delta_schema.py --config config/default.yaml --init
  python fraud_graph_delta_schema.py --config config/default.yaml --reset --force
"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from config_loader import load_config

# Check PySpark availability
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import (
        ArrayType,
        BooleanType,
        DecimalType,
        DoubleType,
        IntegerType,
        LongType,
        StringType,
        StructField,
        StructType,
        TimestampType,
    )
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fraud_graph_delta_schema")


# =============================================================================
# PySpark StructType Schemas (when PySpark is available)
# =============================================================================

def get_spark_schemas() -> Dict[str, Any]:
    """Returns PySpark StructType for each table."""
    if not PYSPARK_AVAILABLE:
        raise RuntimeError("PySpark is required for StructType objects.")

    return {
        "bronze_transactions": StructType([
            StructField("raw_json", StringType(), False),
            StructField("topic", StringType(), False),
            StructField("partition", IntegerType(), False),
            StructField("offset", LongType(), False),
            StructField("ingest_time", TimestampType(), False),
            StructField("dt", StringType(), False),
        ]),
        "silver_transactions": StructType([
            StructField("transaction_id", StringType(), False),
            StructField("src", StringType(), False),
            StructField("dst", StringType(), False),
            StructField("amount", DecimalType(18, 2), False),
            StructField("currency", StringType(), False),
            StructField("operation_type", StringType(), False),
            StructField("event_time", TimestampType(), False),
            StructField("ingest_time", TimestampType(), False),
            StructField("payload_hash", StringType(), False),
            StructField("online_eligible", BooleanType(), False),
            StructField("dt", StringType(), False),
        ]),
        "quarantined_transactions": StructType([
            StructField("source_identity", StringType(), True),
            StructField("raw_json", StringType(), False),
            StructField("reason_codes", ArrayType(StringType()), False),
            StructField("recorded_at", TimestampType(), False),
            StructField("dt", StringType(), False),
        ]),
        "fraud_alerts": StructType([
            StructField("alert_id", StringType(), False),
            StructField("cycle_id", StringType(), False),
            StructField("rule_id", StringType(), False),
            StructField("rule_version", IntegerType(), False),
            StructField("risk_level", StringType(), False),
            StructField("evidence_json", StringType(), False),
            StructField("reason_codes", ArrayType(StringType()), False),
            StructField("first_detected_at", TimestampType(), False),
            StructField("event_min", TimestampType(), False),
            StructField("event_max", TimestampType(), False),
            StructField("dt", StringType(), False),
        ]),
        "anomaly_vertices": StructType([
            StructField("alert_id", StringType(), False),
            StructField("account_id", StringType(), False),
            StructField("risk_level", StringType(), False),
            StructField("dt", StringType(), False),
        ]),
        "anomaly_edges": StructType([
            StructField("alert_id", StringType(), False),
            StructField("transaction_id", StringType(), False),
            StructField("src", StringType(), False),
            StructField("dst", StringType(), False),
            StructField("amount", DecimalType(18, 2), False),
            StructField("currency", StringType(), False),
            StructField("event_time", TimestampType(), False),
            StructField("risk_level", StringType(), False),
            StructField("dt", StringType(), False),
        ]),
        "graph_snapshots": StructType([
            StructField("snapshot_id", StringType(), False),
            StructField("graph_start", TimestampType(), False),
            StructField("graph_end", TimestampType(), False),
            StructField("computed_at", TimestampType(), False),
            StructField("vertex_count", LongType(), False),
            StructField("edge_count", LongType(), False),
            StructField("parameters", StringType(), False),
            StructField("dt", StringType(), False),
        ]),
        "account_graph_metrics": StructType([
            StructField("snapshot_id", StringType(), False),
            StructField("account_id", StringType(), False),
            StructField("pagerank", DoubleType(), False),
            StructField("component_id", LongType(), False),
            StructField("computed_at", TimestampType(), False),
            StructField("dt", StringType(), False),
        ]),
        "processing_progress": StructType([
            StructField("worker_id", StringType(), False),
            StructField("source_position", StringType(), False),
            StructField("high_water_mark", TimestampType(), True),
            StructField("updated_at", TimestampType(), False),
        ]),
        "publication_progress": StructType([
            StructField("alert_id", StringType(), False),
            StructField("published_at", TimestampType(), False),
            StructField("attempt_metadata", StringType(), True),
        ]),
    }


# =============================================================================
# SQL DDL & Partition Metadata
# =============================================================================

TABLE_METADATA = {
    "bronze_transactions": {
        "partitions": ["dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                raw_json STRING,
                topic STRING,
                partition INT,
                offset BIGINT,
                ingest_time TIMESTAMP,
                dt STRING
            ) USING DELTA PARTITIONED BY (dt)
        """,
    },
    "silver_transactions": {
        "partitions": ["dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                transaction_id STRING,
                src STRING,
                dst STRING,
                amount DECIMAL(18,2),
                currency STRING,
                operation_type STRING,
                event_time TIMESTAMP,
                ingest_time TIMESTAMP,
                payload_hash STRING,
                online_eligible BOOLEAN,
                dt STRING
            ) USING DELTA PARTITIONED BY (dt)
        """,
    },
    "quarantined_transactions": {
        "partitions": ["dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                source_identity STRING,
                raw_json STRING,
                reason_codes ARRAY<STRING>,
                recorded_at TIMESTAMP,
                dt STRING
            ) USING DELTA PARTITIONED BY (dt)
        """,
    },
    "fraud_alerts": {
        "partitions": ["risk_level", "dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                alert_id STRING,
                cycle_id STRING,
                rule_id STRING,
                rule_version INT,
                risk_level STRING,
                evidence_json STRING,
                reason_codes ARRAY<STRING>,
                first_detected_at TIMESTAMP,
                event_min TIMESTAMP,
                event_max TIMESTAMP,
                dt STRING
            ) USING DELTA PARTITIONED BY (risk_level, dt)
        """,
    },
    "anomaly_vertices": {
        "partitions": ["risk_level", "dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                alert_id STRING,
                account_id STRING,
                risk_level STRING,
                dt STRING
            ) USING DELTA PARTITIONED BY (risk_level, dt)
        """,
    },
    "anomaly_edges": {
        "partitions": ["risk_level", "dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                alert_id STRING,
                transaction_id STRING,
                src STRING,
                dst STRING,
                amount DECIMAL(18,2),
                currency STRING,
                event_time TIMESTAMP,
                risk_level STRING,
                dt STRING
            ) USING DELTA PARTITIONED BY (risk_level, dt)
        """,
    },
    "graph_snapshots": {
        "partitions": ["dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                snapshot_id STRING,
                graph_start TIMESTAMP,
                graph_end TIMESTAMP,
                computed_at TIMESTAMP,
                vertex_count BIGINT,
                edge_count BIGINT,
                parameters STRING,
                dt STRING
            ) USING DELTA PARTITIONED BY (dt)
        """,
    },
    "account_graph_metrics": {
        "partitions": ["dt"],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                snapshot_id STRING,
                account_id STRING,
                pagerank DOUBLE,
                component_id BIGINT,
                computed_at TIMESTAMP,
                dt STRING
            ) USING DELTA PARTITIONED BY (dt)
        """,
    },
    "processing_progress": {
        "partitions": [],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                worker_id STRING,
                source_position STRING,
                high_water_mark TIMESTAMP,
                updated_at TIMESTAMP
            ) USING DELTA
        """,
    },
    "publication_progress": {
        "partitions": [],
        "ddl": """
            CREATE TABLE IF NOT EXISTS {table} (
                alert_id STRING,
                published_at TIMESTAMP,
                attempt_metadata STRING
            ) USING DELTA
        """,
    },
}


def init_tables(config: Dict[str, Any], spark: Optional[Any] = None) -> None:
    """
    Initializes all 10 Delta Lake tables.
    If Spark is running, executes Delta table creation queries.
    Also ensures directory structure and DDL schemas are safely saved.
    """
    tables_cfg = config.get("storage", {}).get("tables", {})
    delta_base_str = os.environ.get(
        "DELTA_BASE_PATH",
        config.get("storage", {}).get("delta_base", "data/delta")
    )
    delta_base = Path(delta_base_str)

    logger.info(f"Initializing Delta Lake tables in base directory: {delta_base}")

    schema_doc = []
    schema_doc.append("# Delta Lake Schema Definitions\n")

    for table_name, meta in TABLE_METADATA.items():
        table_path = Path(tables_cfg.get(table_name, delta_base / table_name))
        table_path.mkdir(parents=True, exist_ok=True)

        partitions = meta["partitions"]
        ddl = meta["ddl"].strip().replace("{table}", f"`{table_name}`")

        logger.info(f"  [OK] Table '{table_name}': {table_path} (Partitions: {partitions})")
        schema_doc.append(f"## `{table_name}`\n- Path: `{table_path}`\n- Partitions: `{partitions}`\n```sql\n{ddl}\n```\n")

        if spark and PYSPARK_AVAILABLE:
            try:
                # If running inside a Spark session with Delta extension
                empty_df = spark.createDataFrame([], get_spark_schemas()[table_name])
                writer = empty_df.write.format("delta").mode("ignore")
                if partitions:
                    writer = writer.partitionBy(*partitions)
                writer.save(str(table_path))
                logger.info(f"       -> Delta metadata initialized via Spark at {table_path}")
            except Exception as e:
                logger.warning(f"       -> Note on Spark Delta init for {table_name}: {e}")

    # Write DDL documentation file
    ddl_file = delta_base / "delta_schemas.sql"
    with open(ddl_file, "w", encoding="utf-8") as f:
        for table_name, meta in TABLE_METADATA.items():
            f.write(meta["ddl"].strip().replace("{table}", f"`{table_name}`") + ";\n\n")
    logger.info(f"Saved complete Delta SQL DDL file to: {ddl_file}")


def reset_tables(config: Dict[str, Any], force: bool = False) -> None:
    """
    Destructive reset of Delta tables. Requires explicit --force confirmation.
    """
    if not force:
        logger.error("Destructive reset aborted: Must specify --force to confirm deletion of Delta tables.")
        sys.exit(1)

    tables_cfg = config.get("storage", {}).get("tables", {})
    logger.warning("Executing DESTRUCTIVE reset of all Delta tables...")

    for table_name in TABLE_METADATA.keys():
        table_path = Path(tables_cfg.get(table_name, f"data/delta/{table_name}"))
        if table_path.exists():
            shutil.rmtree(table_path, ignore_errors=True)
            logger.info(f"  Removed table directory: {table_path}")

    logger.info("Reset complete.")


def main():
    parser = argparse.ArgumentParser(description="Delta Lake Schema Manager (Mini-Projet 17)")
    parser.add_argument("--config", default="config/default.yaml", help="Path to config YAML")
    parser.add_argument("--init", action="store_true", help="Idempotent creation of Delta tables")
    parser.add_argument("--reset", action="store_true", help="Destructive reset of Delta tables")
    parser.add_argument("--force", action="store_true", help="Confirm destructive reset")

    args = parser.parse_args()
    config = load_config(args.config)

    if args.reset:
        reset_tables(config, force=args.force)
        if args.init:
            init_tables(config)
    elif args.init:
        init_tables(config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
