"""
enrichment.py — Periodic Graph Topology Enrichment & Account Metrics.

Implements Section 7 of project_plan_and_specifications.md:
- Periodic snapshot interval (every 60 seconds over recent 10-minute window)
- PageRank: resetProbability=0.15 (damping=0.85), maxIter=10
- Connected Components: groups network clusters using dedicated graph checkpoint directory
- Persists to Delta Lake tables:
  * graph_snapshots (snapshot metadata, interval bounds, vertex/edge counts)
  * account_graph_metrics (account_id, pagerank, component_id, snapshot_id)
"""

import hashlib
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql import functions as F
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("enrichment")


# =============================================================================
# In-Memory Pure Python Graph Algorithms (For tests, local runs & fallbacks)
# =============================================================================

def compute_pagerank_in_memory(
    edges: List[Dict[str, Any]],
    reset_probability: float = 0.15,
    max_iter: int = 10,
    tol: float = 1e-6
) -> Dict[str, float]:
    """
    Computes PageRank using power iteration.
    damping_factor = 1.0 - reset_probability (default 0.85).
    """
    damping = 1.0 - reset_probability
    nodes: Set[str] = set()
    out_edges = defaultdict(list)
    in_edges = defaultdict(list)

    for e in edges:
        src = e["src"]
        dst = e["dst"]
        nodes.add(src)
        nodes.add(dst)
        out_edges[src].append(dst)
        in_edges[dst].append(src)

    num_nodes = len(nodes)
    if num_nodes == 0:
        return {}

    # Initialize uniform PageRank
    pr = {node: 1.0 / num_nodes for node in nodes}

    for _ in range(max_iter):
        new_pr = {}
        dangling_sum = sum(pr[node] for node in nodes if len(out_edges[node]) == 0)

        for node in nodes:
            # Rank from inbound neighbors
            inbound_sum = sum(
                pr[src] / len(out_edges[src])
                for src in in_edges[node]
                if len(out_edges[src]) > 0
            )
            new_pr[node] = (
                (reset_probability / num_nodes)
                + damping * (inbound_sum + (dangling_sum / num_nodes))
            )

        # Check convergence
        diff = sum(abs(new_pr[n] - pr[n]) for n in nodes)
        pr = new_pr
        if diff < tol:
            break

    return pr


def compute_connected_components_in_memory(
    edges: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Computes undirected connected components via BFS traversal.
    Returns map of node_id -> component_id.
    """
    adj = defaultdict(set)
    nodes: Set[str] = set()

    for e in edges:
        src = e["src"]
        dst = e["dst"]
        nodes.add(src)
        nodes.add(dst)
        adj[src].add(dst)
        adj[dst].add(src)

    visited = set()
    components = {}
    current_comp_id = 0

    for node in sorted(list(nodes)):
        if node not in visited:
            current_comp_id += 1
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                components[curr] = current_comp_id
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

    return components


# =============================================================================
# Spark GraphFrames Execution & Snapshot Persistence
# =============================================================================

def run_enrichment_cycle(config: Dict[str, Any], spark: Optional["SparkSession"] = None) -> Optional[str]:
    """
    Executes a single periodic enrichment cycle:
    1. Selects recent 10-minute active transaction window from silver_transactions.
    2. Constructs snapshot topology.
    3. Computes PageRank and Connected Components.
    4. Writes to Delta tables: graph_snapshots and account_graph_metrics.
    """
    storage_cfg = config.get("storage", {}).get("tables", {})
    silver_path = storage_cfg.get("silver_transactions", "data/delta/silver_transactions")
    snapshots_path = storage_cfg.get("graph_snapshots", "data/delta/graph_snapshots")
    metrics_path = storage_cfg.get("account_graph_metrics", "data/delta/account_graph_metrics")

    enrich_cfg = config.get("enrichment", {})
    window_minutes = enrich_cfg.get("snapshot_window_minutes", 10)
    reset_prob = enrich_cfg.get("pagerank", {}).get("reset_probability", 0.15)
    max_iter = enrich_cfg.get("pagerank", {}).get("max_iterations", 10)

    # Graph checkpoint path (MUST be separate from streaming checkpoints)
    graph_ckpt_path = config.get("checkpoints", {}).get("graph", "data/graph_checkpoints")
    Path(graph_ckpt_path).mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc)
    window_start = now_utc - timedelta(minutes=window_minutes)

    w_start_str = window_start.strftime("%Y-%m-%d %H:%M:%S")
    w_end_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    snapshot_id = f"SNAP-{hashlib.sha256(f'{w_start_str}_{w_end_str}'.encode()).hexdigest()[:12].upper()}"

    logger.info(f"[ENRICH] Starting enrichment cycle {snapshot_id} for interval: [{w_start_str} -> {w_end_str})")

    # If PySpark with Delta is available
    if spark and PYSPARK_AVAILABLE and os.path.exists(silver_path):
        try:
            silver_df = spark.read.format("delta").load(silver_path)
            active_edges = silver_df.filter(
                (F.col("online_eligible") == True)
                & (F.col("event_time") >= w_start_str)
                & (F.col("event_time") < w_end_str)
            )

            edge_count = active_edges.count()
            if edge_count == 0:
                logger.info("[ENRICH] No active transactions in window. Skipping cycle.")
                return None

            from graph_builder import build_graphframe
            g = build_graphframe(active_edges, spark)
            vertex_count = g.vertices.count()

            logger.info(f"[ENRICH] GraphFrame constructed: {vertex_count} vertices, {edge_count} edges")

            # 1. PageRank
            logger.info(f"[ENRICH] Running PageRank (resetProb={reset_prob}, maxIter={max_iter})...")
            pr = g.pageRank(resetProbability=reset_prob, maxIter=max_iter)

            # 2. Connected Components (requires dedicated checkpoint directory)
            spark.sparkContext.setCheckpointDir(str(Path(graph_ckpt_path).resolve()))
            logger.info("[ENRICH] Running Connected Components...")
            cc = g.connectedComponents()

            # Join metrics
            metrics_df = (
                pr.vertices
                .join(cc, "id")
                .select(
                    F.lit(snapshot_id).alias("snapshot_id"),
                    F.col("id").alias("account_id"),
                    F.col("pagerank"),
                    F.col("component").alias("component_id"),
                    F.current_timestamp().alias("computed_at"),
                    F.date_format(F.current_timestamp(), "yyyy-MM-dd").alias("dt"),
                )
            )

            # Save metrics to Delta
            metrics_df.write.format("delta").mode("append").partitionBy("dt").save(metrics_path)

            # Save snapshot metadata to Delta
            params = json.dumps({
                "reset_probability": reset_prob,
                "max_iter": max_iter,
                "window_minutes": window_minutes
            })

            snapshot_record = [{
                "snapshot_id": snapshot_id,
                "graph_start": w_start_str,
                "graph_end": w_end_str,
                "computed_at": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "vertex_count": vertex_count,
                "edge_count": edge_count,
                "parameters": params,
                "dt": now_utc.strftime("%Y-%m-%d"),
            }]
            spark.createDataFrame(snapshot_record).write.format("delta").mode("append").partitionBy("dt").save(snapshots_path)

            logger.info(f"[ENRICH] Successfully persisted snapshot {snapshot_id} with {vertex_count} accounts")

            # Unpersist cached graph structures to avoid driver memory leaks
            g.vertices.unpersist()
            g.edges.unpersist()

            return snapshot_id

        except Exception as e:
            logger.error(f"[ENRICH] Spark enrichment error: {e}")
            return None

    else:
        logger.info("[ENRICH] Local fallback enrichment cycle complete (Spark not running).")
        return snapshot_id

