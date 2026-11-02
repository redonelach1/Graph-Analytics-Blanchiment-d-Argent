#!/usr/bin/env python3
"""
Environment Smoke Test — Validates that all stack components work together.

Run inside the spark-app container:
    docker exec -it aml-spark-app python /opt/app/scripts/smoke_test.py

Must pass ALL checks before proceeding to Phase 2.
"""

import sys
import json
import traceback
from datetime import datetime


def log_result(test_name: str, passed: bool, detail: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {test_name}")
    if detail:
        print(f"         {detail}")
    return passed


def main():
    results = []
    print("=" * 70)
    print("  AML Graph Analytics — Environment Smoke Test")
    print(f"  Timestamp: {datetime.utcnow().isoformat()}Z")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Test 1: Spark Session Creation
    # -------------------------------------------------------------------------
    print("\n[1/7] Spark Session + Delta Lake + GraphFrames")
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
        from pyspark.sql.types import (
            StructType, StructField, StringType, DoubleType, TimestampType
        )

        spark = (
            SparkSession.builder
            .appName("AML-SmokeTest")
            .master("local[2]")
            .config("spark.sql.extensions",
                    "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.ui.enabled", "false")
            .getOrCreate()
        )
        results.append(log_result("Spark session created", True,
                                  f"Version: {spark.version}"))
    except Exception as e:
        results.append(log_result("Spark session created", False, str(e)))
        print("\n🛑 Cannot continue without Spark. Aborting.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Test 2: Delta Lake Write / Read
    # -------------------------------------------------------------------------
    print("\n[2/7] Delta Lake Write & Read")
    try:
        delta_path = "/tmp/smoke_test_delta"
        test_data = [("TXN-001", "ACC-A", "ACC-B", 1000.0),
                     ("TXN-002", "ACC-B", "ACC-C", 2000.0),
                     ("TXN-003", "ACC-C", "ACC-A", 1500.0)]
        df = spark.createDataFrame(test_data,
                                   ["txn_id", "src", "dst", "amount"])
        df.write.format("delta").mode("overwrite").save(delta_path)
        read_df = spark.read.format("delta").load(delta_path)
        count = read_df.count()
        assert count == 3, f"Expected 3 rows, got {count}"
        results.append(log_result("Delta write/read", True,
                                  f"{count} rows written and read"))
    except Exception as e:
        results.append(log_result("Delta write/read", False, str(e)))

    # -------------------------------------------------------------------------
    # Test 3: GraphFrame Construction
    # -------------------------------------------------------------------------
    print("\n[3/7] GraphFrame Construction (3 nodes)")
    try:
        from graphframes import GraphFrame

        vertices = spark.createDataFrame(
            [("A",), ("B",), ("C",)], ["id"]
        )
        edges = spark.createDataFrame(
            [("A", "B", "TXN-1", 1000.0),
             ("B", "C", "TXN-2", 2000.0),
             ("C", "A", "TXN-3", 1500.0)],
            ["src", "dst", "txn_id", "amount"]
        )
        g = GraphFrame(vertices, edges)
        assert g.vertices.count() == 3
        assert g.edges.count() == 3
        results.append(log_result("GraphFrame construction", True,
                                  "3 vertices, 3 edges"))
    except Exception as e:
        results.append(log_result("GraphFrame construction", False, str(e)))

    # -------------------------------------------------------------------------
    # Test 4: Motif Finding (Triangle)
    # -------------------------------------------------------------------------
    print("\n[4/7] Motif Finding — Triangle Detection")
    try:
        triangles = g.find("(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)")
        tri_count = triangles.count()
        assert tri_count > 0, f"Expected triangles, got {tri_count}"
        # Filter distinct accounts
        filtered = triangles.filter(
            (F.col("a.id") != F.col("b.id")) &
            (F.col("b.id") != F.col("c.id")) &
            (F.col("a.id") != F.col("c.id"))
        )
        results.append(log_result("Motif finding (triangles)", True,
                                  f"{tri_count} raw matches, "
                                  f"{filtered.count()} distinct-account"))
    except Exception as e:
        results.append(log_result("Motif finding (triangles)", False, str(e)))

    # -------------------------------------------------------------------------
    # Test 5: PageRank
    # -------------------------------------------------------------------------
    print("\n[5/7] PageRank")
    try:
        pr = g.pageRank(resetProbability=0.15, maxIter=10)
        pr_count = pr.vertices.count()
        assert pr_count == 3, f"Expected 3 vertices, got {pr_count}"
        pr.vertices.select("id", "pagerank").show(truncate=False)
        results.append(log_result("PageRank", True,
                                  f"{pr_count} vertices scored"))
    except Exception as e:
        results.append(log_result("PageRank", False, str(e)))

    # -------------------------------------------------------------------------
    # Test 6: Connected Components
    # -------------------------------------------------------------------------
    print("\n[6/7] Connected Components")
    try:
        spark.sparkContext.setCheckpointDir("/tmp/smoke_graphframes_ckpt")
        cc = g.connectedComponents()
        cc_count = cc.count()
        assert cc_count == 3
        components = cc.select("component").distinct().count()
        results.append(log_result("Connected components", True,
                                  f"{cc_count} vertices, "
                                  f"{components} component(s)"))
    except Exception as e:
        results.append(log_result("Connected components", False, str(e)))

    # -------------------------------------------------------------------------
    # Test 7: Kafka Connectivity
    # -------------------------------------------------------------------------
    print("\n[7/7] Kafka Connectivity")
    try:
        from confluent_kafka.admin import AdminClient
        import os

        bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9094")
        admin = AdminClient({"bootstrap.servers": bootstrap})
        metadata = admin.list_topics(timeout=10)
        topics = list(metadata.topics.keys())
        has_txn = "financial-transactions" in topics
        has_alerts = "fraud-alerts" in topics
        results.append(log_result("Kafka connection", True,
                                  f"Topics: {topics}"))
        results.append(log_result("Topic 'financial-transactions' exists",
                                  has_txn))
        results.append(log_result("Topic 'fraud-alerts' exists", has_alerts))
    except Exception as e:
        results.append(log_result("Kafka connectivity", False, str(e)))

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    passed = sum(1 for r in results if r)
    total = len(results)
    all_passed = all(results)
    status = "ALL TESTS PASSED ✅" if all_passed else "SOME TESTS FAILED ❌"
    print(f"  RESULT: {passed}/{total} checks passed — {status}")
    print("=" * 70)

    spark.stop()

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()

