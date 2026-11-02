# ⚠️ System Limitations & Architectural Trade-offs

This document explicitly catalogues known constraints, assumptions, and architectural boundaries of the AML Graph Analytics system, fulfilling the transparency requirements of Section 13.

---

## 1. Cycle Length Specificity (Triangular Motifs)

- **Scope:** The online detection engine actively detects directed 3-cycles ($A \to B \to C \to A$).
- **Rationale:** Directed triangles represent the fundamental building block of fast money-mule layering structures. In real-time streaming, searching for arbitrary length $k$-cycles ($k \ge 5$) exhibits factorial combinatorial complexity $\mathcal{O}(V^k)$, making continuous 30-second sliding micro-batch execution computationally infeasible on commodity hardware.
- **Mitigation:** Graph enrichment runs periodic connected component clustering (`component_id`), which identifies larger multi-hop money-laundering rings and subgraphs offline even if the constituent transactions span broader topologies.

---

## 2. GraphFrames Streaming Integration Pattern

- **Constraint:** GraphFrames is fundamentally a batch graph analysis library; it does not natively maintain stateful incremental streaming graphs across continuous micro-batches.
- **Architectural Solution:** The pipeline uses `foreachBatch` on the `silver_transactions` stream. For each batch, it reads the active $[start, end)$ 10-minute slice, materializes node and edge dataframes, and applies motif queries. 
- **Performance Trade-off:** While this guarantees ACID consistency and idempotent recovery via Delta Lake, extremely large active window edge counts ($> 500,000$ edges per 10-minute window) would require horizontal Spark worker scaling or dedicated graph OLAP engines (e.g., TigerGraph / Neo4j).

---

## 3. Checkpoint Isolation Requirement

- **Requirement:** GraphFrames' `connectedComponents` algorithm internally requires `sc.setCheckpointDir(...)` to truncate lineage during iterative graph contraction.
- **Risk:** If the connected components checkpoint shares the same directory as Spark Structured Streaming (`data/checkpoints`), the iterative GraphFrames job will overwrite and corrupt streaming offset logs, causing fatal stream deserialization failures on restart.
- **Mandatory Configuration:** The system strictly isolates:
  - Streaming offsets: `data/checkpoints/`
  - GraphFrames internal checkpoints: `data/graph_checkpoints/`

---

## 4. Single-Currency Homogeneity Assumption

- **Constraint:** The baseline detection rule `TEMPORAL_TRIANGLE` enforces strict single-currency matching (`SAME_CURRENCY`, default `MAD`).
- **Rationale:** Laundering loops that attempt currency arbitrage or rapid FX exchanges within a 10-minute window without registered FX transaction rates can skew ratio balance calculations.
- **Future Extension:** Multi-currency cycles require an integrated live FX conversion feed with rate snapshotting at event time to normalize edge values.

---

## 5. Event-Time vs Wall-Clock Watermark Bounds (AT-21)

- **Behavior:** The watermark $W = H - 120s$ is strictly event-time driven.
- **Impact on Idle Feeds:** During periods where no transactions are transmitted over Kafka, the system does not artificially advance the watermark based on host clock drift. Consequently, if a stream is paused and resumed hours later, transactions with timestamps shortly prior to the pause will still be correctly accepted rather than dropped as expired.

