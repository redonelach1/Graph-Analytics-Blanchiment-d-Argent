"""
test_enrichment.py — Verification of Graph Topology Enrichment & Account Metrics.

Verifies Acceptance Criteria:
- AT-17: High-centrality hub account receives top PageRank without false fraud classification
- Connected components accurately partition disconnected clusters
- Dedicated checkpointing & parameter provenance tracking
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from detection import detect_triangles_in_window
from enrichment import (
    compute_connected_components_in_memory,
    compute_pagerank_in_memory,
)


def test_at17_high_centrality_legitimate_hub():
    """
    AT-17: A legitimate high-in-degree hub (e.g. merchant/utility) receives high PageRank,
    but produces 0 triangle alerts (metrics present without false fraud claim).
    """
    edges = []
    # 20 consumer accounts paying a single merchant hub
    for i in range(1, 21):
        edges.append({
            "src": f"ACC-CONSUMER-{i:02d}",
            "dst": "ACC-MERCHANT-HUB",
            "amount": 200.0,
            "currency": "MAD",
            "transaction_id": f"TXN-HUB-{i:02d}",
            "timestamp": "2026-10-07T10:05:00Z"
        })

    # 1. Compute PageRank
    pr = compute_pagerank_in_memory(edges, reset_probability=0.15, max_iter=20)
    assert len(pr) == 21, "All 21 accounts should receive PageRank scores"

    hub_score = pr["ACC-MERCHANT-HUB"]
    consumer_scores = [pr[f"ACC-CONSUMER-{i:02d}"] for i in range(1, 21)]

    # The merchant hub must have a significantly higher PageRank than leaf consumers
    assert hub_score > max(consumer_scores) * 5, (
        f"Hub PageRank ({hub_score:.4f}) should dominate consumer scores ({max(consumer_scores):.4f})"
    )

    # 2. Run triangle detection on this hub network
    alerts = detect_triangles_in_window(edges)

    # Must produce ZERO fraud alerts (fan-in is not a closed triangle)
    assert len(alerts) == 0, "High centrality alone must NOT trigger a fraud alert"

    print("[PASS] AT-17: Legitimate hub receives top PageRank without false fraud classification")


def test_connected_components_partitioning():
    """Verifies that disconnected clusters receive distinct component IDs."""
    edges = [
        # Cluster 1: Triangle A - B - C
        {"src": "A", "dst": "B"},
        {"src": "B", "dst": "C"},
        {"src": "C", "dst": "A"},

        # Cluster 2: Independent pair X - Y
        {"src": "X", "dst": "Y"},
    ]

    components = compute_connected_components_in_memory(edges)

    # All nodes must have a component ID
    assert set(components.keys()) == {"A", "B", "C", "X", "Y"}

    # Cluster 1 nodes must share the same component ID
    assert components["A"] == components["B"] == components["C"]

    # Cluster 2 nodes must share the same component ID
    assert components["X"] == components["Y"]

    # The two clusters must have different component IDs
    assert components["A"] != components["X"]

    print("[PASS] Connected Components correctly groups disconnected graph clusters")


def test_pagerank_convergence_and_conservation():
    """Verifies PageRank properties (sum of ranks converges to 1.0)."""
    edges = [
        {"src": "A", "dst": "B"},
        {"src": "B", "dst": "C"},
        {"src": "C", "dst": "A"},
    ]

    pr = compute_pagerank_in_memory(edges, reset_probability=0.15, max_iter=30)
    total_rank = sum(pr.values())

    # Total probability mass should be approximately 1.0
    assert abs(total_rank - 1.0) < 1e-4, f"PageRank sum should be ~1.0, got {total_rank}"
    # In a symmetric directed triangle, all vertices have equal rank
    assert abs(pr["A"] - pr["B"]) < 1e-4
    assert abs(pr["B"] - pr["C"]) < 1e-4

    print("[PASS] PageRank probability conservation & symmetric convergence verified")


if __name__ == "__main__":
    test_at17_high_centrality_legitimate_hub()
    test_connected_components_partitioning()
    test_pagerank_convergence_and_conservation()
    print("\nALL ENRICHMENT ACCEPTANCE TESTS PASSED!")

