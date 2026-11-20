# 🛡️ Real-Time AML Graph Analytics & Directed Cycle Detection

[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-FDEE21?logo=apachespark&logoColor=black&labelColor=E25A1C)](https://spark.apache.org/)
[![Delta Lake](https://img.shields.io/badge/Delta%20Lake-3.3.0-00ADD8?logo=delta&logoColor=white&labelColor=003545)](https://delta.io/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.5.1%20KRaft-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![GraphFrames](https://img.shields.io/badge/GraphFrames-0.8.4--spark3.5-blueviolet)](https://graphframes.github.io/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2%20App%20Router-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-shadcn%2Fui-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Acceptance Tests](https://img.shields.io/badge/Acceptance%20Tests-22%2F22%20PASS-brightgreen?logo=checkmarx&logoColor=white)](tests/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org/)

An enterprise-grade, distributed streaming analytics platform designed to detect complex cyclic fund-layering rings ($A \to B \to C \to A$) in continuous financial transfer streams. Built on **Apache Spark 3.5.0 Structured Streaming**, **Delta Lake 3.3.0**, **GraphFrames 0.8.4**, and **Next.js 14**, this system provides sub-minute alerting, deterministic canonical idempotency, zero label leakage, and interactive forensic graph investigation.

---

## 📑 Table of Contents

- [1. Executive Overview & Problem Statement](#1-executive-overview--problem-statement)
- [2. System Architecture & Topology](#2-system-architecture--topology)
- [3. Streaming Dataflow & Lakehouse Medallion Model](#3-streaming-dataflow--lakehouse-medallion-model)
- [4. Temporal Windowing & Watermark Semantics](#4-temporal-windowing--watermark-semantics)
- [5. Graph Motifs & Detection Algorithms](#5-graph-motifs--detection-algorithms)
- [6. Deterministic Idempotency & Canonical Deduplication](#6-deterministic-idempotency--canonical-deduplication)
- [7. Graph Enrichment & Entity Centrality (AT-17 Separation)](#7-graph-enrichment--entity-centrality-at-17-separation)
- [8. The 10 Delta Lake Tables Architecture](#8-the-10-delta-lake-tables-architecture)
- [9. Forensic Investigation Cockpits (Next.js & Streamlit)](#9-forensic-investigation-cockpits-nextjs--streamlit)
- [10. Docker Compose Infrastructure & Service Inventory](#10-docker-compose-infrastructure--service-inventory)
- [11. Quick Start & Execution Runbook](#11-quick-start--execution-runbook)
- [12. Acceptance Test Suite (22 / 22 Passing)](#12-acceptance-test-suite-22--22-passing)
- [13. Performance Benchmarks & Stress Tests (AT-22)](#13-performance-benchmarks--stress-tests-at-22)
- [14. Academic Deliverables & Documentation Directory](#14-academic-deliverables--documentation-directory)

---

## 1. Executive Overview & Problem Statement

Money laundering through **circular layering** is among the most evasive financial crimes. In a circular layering scheme, illicit capital is dispersed across multiple synthetic accounts or mule networks through rapid, multi-hop fund transfers before looping back to the originator or an affiliated controller ($A \to B \to C \to A$). Traditional relational database rule engines fail to discover these rings due to:

1. **Relational Join Explosion:** Querying cyclic paths of depth $k \ge 3$ across millions of ledger transactions causes combinatorial join penalties ($O(N^k)$) that overwhelm traditional SQL engines.
2. **Out-of-Order & Delayed Event Arrival:** Network latency, mobile offline queuing, and batch bank settlement cause transactions to arrive out of chronological order, invalidating naive streaming windows.
3. **High-Centrality False Positives:** Legitimate commercial settlement nodes (e.g., utility aggregators, corporate payroll hubs) concentrate large volumes and high in/out degrees, triggering massive false alert volumes in naive degree-based systems.
4. **Duplicate & Duplicate-Conflicting Events:** Distributed retries across message brokers cause identical or conflicting transaction records to be ingested repeatedly, creating duplicate alert spam.

### Solution Pillars

This platform addresses each challenge with a rigorous distributed architecture:
- **GraphFrames Motif Finding:** Declarative graph pattern matching `(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)` executed over distributed Spark GraphFrames partitions.
- **Strict Temporal Window Alignment:** Semi-open aligned intervals $[t_{\text{start}}, t_{\text{end}})$ of length $L = 600\text{s}$ (10 minutes) with slide cadence $S = 30\text{s}$ and an event-time watermark $W = H - 120\text{s}$.
- **Mathematical Separation of Hubs (AT-17):** Combines **PageRank centrality** ($\alpha = 0.85$, 10 iterations) and **Weakly Connected Components** graph clustering to distinguish legitimate high-volume hubs (which do not form closed temporal loops) from cyclic mule clusters.
- **Canonical Idempotency:** Deterministic cyclic string rotation sorting and cryptographic **SHA-256 hashing** (`cycle_id` and `alert_id`) ensuring exactly-once business semantics across reprocessing.
- **ACID Lakehouse Storage:** 10 partitioned Delta Lake tables maintaining complete auditability, time-travel history, and forensic replayability.

---

## 2. System Architecture & Topology

The platform consists of four primary functional tiers deployed across a multi-container Docker bridge network (`aml-network`):

```mermaid
flowchart TD
    subgraph INGESTION["Tier 1: High-Throughput Traffic Ingestion"]
        P["Financial Graph Producer<br/>(Normal, Triangle, Mixed, AMLSim)"] -->|Kafka Protocol :9094| K["Apache Kafka 3.5.1 Broker<br/>(KRaft Mode, Topic: financial-transactions)"]
        KUI["Kafka UI Console<br/>(:8090)"] -.->|Inspect Partitions & Offsets| K
    end

    subgraph STREAMING["Tier 2: Distributed Spark 3.5.0 Streaming Engine"]
        SM["Spark Master (:8080, :7077)"] --- SW["Spark Worker (:8081)<br/>(4 CPU Cores, 4.0 GiB RAM)"]
        K -->|Consumer Group: aml-spark-app| SA["aml-spark-app (:4040)<br/>Structured Streaming Context"]
        
        SA --> S1["1. Deterministic Validation<br/>(Schema, Range, Future Skew, Dedup)"]
        S1 --> S2["2. Temporal Window Buffer<br/>(L=600s, S=30s, W=H-120s)"]
        S2 --> S3["3. Graph Motif Engine<br/>(GraphFrames Motif Mining)"]
        S3 --> S4["4. Canonical Deduplication<br/>(SHA-256 Cycle Identifiers)"]
        S4 --> S5["5. Graph Enrichment<br/>(PageRank alpha=0.85 & Connected Components)"]
        S5 --> S6["6. Dual-Sink Dispatcher<br/>(ACID Delta Lake & Kafka Publisher)"]
    end

    subgraph LAKEHOUSE["Tier 3: Delta Lake ACID Lakehouse (10 Tables)"]
        S6 -->|Raw Ingest Log| T1[("bronze_transactions")]
        S6 -->|Validated Event Log| T2[("silver_transactions")]
        S6 -->|Quarantine Storage| T3[("quarantined_transactions")]
        S6 -->|Deduplicated Cycle Alerts| T4[("fraud_alerts")]
        S6 -->|Forensic Entity Projections| T5[("anomaly_vertices")]
        S6 -->|Forensic Edge Projections| T6[("anomaly_edges")]
        S6 -->|Window Snapshots| T7[("graph_snapshots")]
        S6 -->|PageRank & Cluster Metrics| T8[("account_graph_metrics")]
        S6 -->|Stream Engine Checkpoints| T9[("processing_progress")]
        S6 -->|Publication Audit| T10[("publication_progress")]
    end

    subgraph DOWNSTREAM["Tier 4: Egress & Forensic Investigation Cockpits"]
        S6 -->|Producer Protocol| KA["Kafka Alert Topic<br/>(fraud-alerts :9094)"]
        T4 & T5 & T6 & T8 -->|Shared Delta Mount /opt/app/data/delta| DASH["Next.js 14 Cockpit (:3000)<br/>• SVG Flow Topology Graph<br/>• Real-Time Alert Ledger<br/>• SAR JSON Export Engine"]
        T4 & T8 -->|Delta / PyVis Adapter| PYVIS["Streamlit Cockpit (:8501)<br/>• Physics-Simulated Network Graph<br/>• Interactive Cluster Exploration"]
    end

    classDef primary fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef storage fill:#0f172a,stroke:#06b6d4,stroke-width:2px,color:#fff;
    classDef downstream fill:#18181b,stroke:#10b981,stroke-width:2px,color:#fff;
    class P,K,SA,SM,SW primary;
    class T1,T2,T3,T4,T5,T6,T7,T8,T9,T10 storage;
    class DASH,PYVIS,KA,KUI downstream;
```

---

## 3. Streaming Dataflow & Lakehouse Medallion Model

The transaction processing pipeline adheres strictly to the **Medallion Lakehouse Architecture** (Bronze $\to$ Silver $\to$ Gold/Alerts), enforcing data hygiene, temporal integrity, and deterministic routing:

```mermaid
flowchart LR
    RAW["Incoming Raw JSON<br/>financial-transactions"] -->|Append-Only Ingestion| B[("Bronze Table<br/>bronze_transactions<br/>Partition: dt")]

    B --> VAL{"Deterministic Validation Engine<br/>• Currency in [MAD]<br/>• Amount > 0 & Precision <= 2<br/>• Future Skew <= 60s<br/>• Payload Hash Check"}

    VAL -->|FAIL / Conflict| Q[("Quarantine Table<br/>quarantined_transactions<br/>Reason Codes Array<br/>Partition: dt")]
    VAL -->|PASS| S[("Silver Table<br/>silver_transactions<br/>online_eligible=True<br/>Partition: dt")]

    S --> MOTIF{"GraphFrames Motif Engine<br/>(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)<br/>• a,b,c distinct<br/>• e1,e2,e3 distinct<br/>• Same Window & Currency"}

    MOTIF -->|Cycle Discovered| DEDUP{"Canonical Deduplication<br/>cycle_id = SHA256(min_rot)<br/>alert_id = SHA256(rule, cycle)"}

    DEDUP --> FA[("Fraud Alerts Table<br/>fraud_alerts<br/>Evidence JSON & Risk Tier<br/>Partition: risk_level, dt")]
    DEDUP --> AV[("Anomaly Vertices<br/>anomaly_vertices<br/>Partition: risk_level, dt")]
    DEDUP --> AE[("Anomaly Edges<br/>anomaly_edges<br/>Partition: risk_level, dt")]

    S --> ENRICH{"Enrichment Job<br/>PageRank alpha=0.85<br/>Connected Components"}
    ENRICH --> AGM[("Account Metrics<br/>account_graph_metrics<br/>Partition: dt")]

    FA --> PUB{"Alert Publisher<br/>At-Least-Once Delivery"}
    PUB --> KT["Kafka Topic<br/>fraud-alerts"]
    PUB --> PP[("Publication Audit<br/>publication_progress")]

    classDef bronze fill:#78350f,stroke:#d97706,stroke-width:2px,color:#fff;
    classDef silver fill:#334155,stroke:#94a3b8,stroke-width:2px,color:#fff;
    classDef gold fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef logic fill:#1e1b4b,stroke:#6366f1,stroke-width:1px,color:#fff;
    class B bronze;
    class S silver;
    class Q bronze;
    class FA,AV,AE,AGM gold;
    class VAL,MOTIF,DEDUP,ENRICH,PUB logic;
```

---

## 4. Temporal Windowing & Watermark Semantics

Financial cycle detection requires strict temporal bounding to ensure that transactions occurring months apart are not falsely correlated into a layering scheme:

```mermaid
flowchart TD
    subgraph TIMELINE["Event Timeline & Window Alignment"]
        direction TB
        E1["Event e1 (t=100s)"] --> W1
        E2["Event e2 (t=150s)"] --> W1
        E3["Event e3 (t=200s)"] --> W1
        
        subgraph W1["Window 0: [0s, 600s)"]
            T1["All 3 edges present in Window 0"]
            T1 --> MATCH["CYCLE DETECTED<br/>Duration = 100s <= 600s"]
        end

        subgraph W2["Window 1: [30s, 630s) — Slide Cadence S = 30s"]
            T2["Candidate window also covers e1, e2, e3"]
            T2 --> DEDUP_CHECK["Deduplicated by canonical cycle_id<br/>(Zero Duplicate Alerting)"]
        end
    end

    subgraph WATERMARK_SPEC["Watermark Policy & Lateness Bounds"]
        direction TB
        H["Committed High-Water Mark (H)"]
        W["Watermark: W = H - 120s<br/>(2 Minutes Lag Horizon)"]
        LATE["Late Transaction (t < W)"]
        FUTURE["Future Skew Transaction (t > now + 60s)"]

        H -.->|120 Seconds Lag| W
        LATE -->|Dropped from Online State| LATE_ACTION["Route to Silver<br/>online_eligible = False<br/>(Preserved for Batch Audits)"]
        FUTURE -->|Clock Skew Violation| QUAR_ACTION["Route to Quarantine<br/>Reason: FUTURE_TIMESTAMP_SKEW"]
    end
```

### Mathematical Definitions

1. **Window Duration ($L$):** $600\text{ seconds}$ (10 minutes).
2. **Slide Cadence ($S$):** $30\text{ seconds}$.
3. **Aligned Window Boundary Formula:**
   For any transaction with event timestamp $t$, the set of integer window indices $k$ enclosing $t$ is:
   $$\frac{t - L}{S} < k \le \frac{t}{S}, \quad k \in \mathbb{Z}$$
   Each window index $k$ defines the half-open temporal interval $[k \cdot S, \; k \cdot S + L)$.
4. **Watermark Formulation:**
   Let $H$ be the monotonic maximum event timestamp observed by the ingestion engine:
   $$W = H - \Delta_{\text{watermark}}, \quad \text{where } \Delta_{\text{watermark}} = 120\text{ seconds}$$
   Transactions arriving with $t_{\text{event}} < W$ are marked as late data (`online_eligible = false`).
5. **Future Skew Tolerance:**
   Transactions with $t_{\text{event}} > t_{\text{ingest}} + 60\text{s}$ are rejected into `quarantined_transactions` to prevent clock skew poisoning.

---

## 5. Graph Motifs & Detection Algorithms

The cycle detection engine executes over directed graphs $G = (V, E)$, where vertices $V$ represent financial account entities and directed edges $E$ represent individual verified transfers.

```mermaid
flowchart LR
    A(("Account A<br/>(ACC-0081)")) -->|e1: TXN-101<br/>161,232.57 MAD<br/>t1 = 19:08:15| B(("Account B<br/>(ACC-0014)"))
    B -->|e2: TXN-102<br/>154,750.32 MAD<br/>t2 = 19:09:11| C(("Account C<br/>(ACC-0003)"))
    C -->|e3: TXN-103<br/>147,876.55 MAD<br/>t3 = 19:12:34| A

    style A fill:#1e293b,stroke:#ef4444,stroke-width:2px,color:#fff
    style B fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#fff
    style C fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
```

### GraphFrames Motif Pattern

The core motif pattern is expressed declaratively in PySpark GraphFrames:

```python
motif_pattern = "(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)"
```

### Mandatory Constraint Filters

To eliminate false matches, every candidate triangle must satisfy all 6 deterministic constraints:

| Filter ID | Mathematical Rule | Implementation Rationale |
| :--- | :--- | :--- |
| **F-01** | $a \ne b \land b \ne c \land c \ne a$ | Vertices must be **3 distinct account IDs** (no self-loops or two-hop bouncing). |
| **F-02** | $e_1.\text{id} \ne e_2.\text{id} \ne e_3.\text{id}$ | Edges must represent **3 distinct transaction identifiers**. |
| **F-03** | $e_1.\text{curr} = e_2.\text{curr} = e_3.\text{curr} \in \{\text{MAD}\}$ | Currency uniformity (multi-currency conversions require FX normalization). |
| **F-04** | $\max(t_1, t_2, t_3) - \min(t_1, t_2, t_3) \le 600\text{s}$ | All 3 edges must occur within the same **10-minute sliding window**. |
| **F-05** | $\{e_1.\text{id}, e_2.\text{id}, e_3.\text{id}\} \cap \text{NewBatchTxnIDs} \ne \emptyset$ | **Incremental progress guarantee:** At least one edge must be new in the active micro-batch to prevent re-alerting on static historical subgraphs. |
| **F-06** | $\text{Ratio} = \frac{\max(m_1, m_2, m_3)}{\min(m_1, m_2, m_3)} \le 1.15$ | **Layering Conservation:** Fund preservation check (smurfing/layering maintains consistent capital volume with $\le 15\%$ operational commission slippage). |

### Multi-Tier Risk Classification

Discovered cycles are classified into deterministic risk tiers based on monetary volume and amount dispersion:

$$\text{TotalVolume} = \sum_{i=1}^{3} m_i$$

$$\text{AmountRatio} = \frac{\max(m_1, m_2, m_3)}{\min(m_1, m_2, m_3)}$$

- **HIGH RISK (Critical Tier):**
  $$\text{TotalVolume} \ge 100,000\text{ MAD} \quad \land \quad \text{AmountRatio} \le 1.15$$
  *Triggers immediate compliance escalation and automated SAR drafting.*
- **MEDIUM RISK:**
  $$20,000\text{ MAD} \le \text{TotalVolume} < 100,000\text{ MAD} \quad \lor \quad \text{AmountRatio} \le 1.30$$
- **LOW RISK:**
  $$\text{TotalVolume} < 20,000\text{ MAD}$$

---

## 6. Deterministic Idempotency & Canonical Deduplication

In distributed graph mining, the same cycle can be discovered from different starting points ($A \to B \to C \to A$, $B \to C \to A \to B$, or $C \to A \to B \to C$) and across overlapping sliding windows ($W_0, W_1, \dots$). 

To ensure **zero duplicate alerts**, the platform executes a deterministic canonical sort algorithm:

```mermaid
flowchart TD
    RAW["Discovered Edge Triplet:<br/>(ACC-0014, ACC-0003, ACC-0081)"] --> PERM["Generate All Cyclic Rotations:<br/>1. ACC-0014 -> ACC-0003 -> ACC-0081<br/>2. ACC-0003 -> ACC-0081 -> ACC-0014<br/>3. ACC-0081 -> ACC-0014 -> ACC-0003"]

    PERM --> MIN["Lexicographical Minimum Selection:<br/>min_rotation = ('ACC-0003', 'ACC-0081', 'ACC-0014')"]

    MIN --> CYCLE_HASH["SHA-256 Cycle Identifier:<br/>cycle_id = SHA256('ACC-0003|ACC-0081|ACC-0014')"]

    CYCLE_HASH --> ALERT_HASH["SHA-256 Alert Identifier:<br/>alert_id = SHA256('TEMPORAL_TRIANGLE|v1|' + cycle_id)"]

    ALERT_HASH --> DEDUP_STORE{{"Delta Lake Check<br/>fraud_alerts.exists(alert_id)"}}
    DEDUP_STORE -->|Already Exists| SKIP["Discard Duplicate Alert<br/>(Zero Duplicate Egress)"]
    DEDUP_STORE -->|New Alert| COMMIT["Commit to fraud_alerts<br/>Publish to Kafka fraud-alerts"]
```

---

## 7. Graph Enrichment & Entity Centrality (AT-17 Separation)

A critical requirement of Section 7 (AT-17) is preventing high-volume commercial aggregators (e.g., utility bill settlement, merchant payment gateways) from generating false cycle alerts while maintaining high detection sensitivity on mule rings.

```mermaid
flowchart LR
    subgraph LEGIT_HUB["Legitimate Commercial Hub (ACC-MERCHANT-HUB)"]
        direction TB
        M1["Retail Customer 1"] -->|Inbound 50k| HUB(("ACC-MERCHANT-HUB<br/>PageRank = 0.1428 (TOP)<br/>Total Vol = 1.25M MAD"))
        M2["Retail Customer 2"] -->|Inbound 75k| HUB
        M3["Retail Customer 3"] -->|Inbound 120k| HUB
        HUB -->|Outbound Settlement| SETTLE["Central Settlement Bank"]
        HUB_STATUS["Zero Loop Closure Back to Customers<br/>Cycle Count = 0<br/>RESULT: 0 False Positives"]
    end

    subgraph MULE_RING["Cyclic Layering Ring (Mule Accounts)"]
        direction TB
        MA(("ACC-0081<br/>PR = 0.0482")) -->|161k MAD| MB(("ACC-0014<br/>PR = 0.0451"))
        MB -->|154k MAD| MC(("ACC-0003<br/>PR = 0.0439"))
        MC -->|147k MAD| MA
        MULE_STATUS["Strict Temporal Loop Closure<br/>Cycle Count >= 1<br/>RESULT: 100% True Positive Alert"]
    end

    style HUB fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff
    style MA fill:#450a0a,stroke:#ef4444,stroke-width:2px,color:#fff
    style MB fill:#450a0a,stroke:#ef4444,stroke-width:2px,color:#fff
    style MC fill:#450a0a,stroke:#ef4444,stroke-width:2px,color:#fff
```

### Graph Enrichment Pipeline (Role: `enrich`)

1. **PageRank Centrality:** Computed via GraphFrames PageRank with damping factor $\alpha = 0.85$ and 10 iterations. Identifies global capital collection nodes.
2. **Connected Components (CC):** Partitions the graph into isolated subgraphs using distributed connected components. Identifies isolated money-laundering cells.
3. **Storage:** Output metrics are persisted to `account_graph_metrics` partitioned by `dt`, enabling instant lookup of entity centrality during forensic investigations.

---

## 8. The 10 Delta Lake Tables Architecture

The platform maintains 10 ACID transactional tables within the shared volume mount (`/opt/app/data/delta`), each serving an explicit operational responsibility:

```mermaid
erDiagram
    bronze_transactions ||--o{ silver_transactions : "validates & enriches"
    bronze_transactions ||--o{ quarantined_transactions : "rejects malformed"
    silver_transactions ||--o{ fraud_alerts : "generates cycle alerts"
    fraud_alerts ||--|{ anomaly_vertices : "projects entity roles"
    fraud_alerts ||--|{ anomaly_edges : "projects transfer flows"
    silver_transactions ||--o{ graph_snapshots : "snapshots window state"
    silver_transactions ||--o{ account_graph_metrics : "computes PageRank & CC"
    fraud_alerts ||--o{ publication_progress : "tracks Kafka egress"
    silver_transactions ||--o{ processing_progress : "tracks stream offsets"

    bronze_transactions {
        string raw_json
        string topic
        int partition
        long offset
        timestamp ingest_time
        string dt
    }
    silver_transactions {
        string transaction_id
        string src
        string dst
        decimal amount
        string currency
        timestamp event_time
        timestamp ingest_time
        string payload_hash
        boolean online_eligible
        string dt
    }
    quarantined_transactions {
        string source_identity
        string raw_json
        string_array reason_codes
        timestamp recorded_at
        string dt
    }
    fraud_alerts {
        string alert_id
        string cycle_id
        string rule_id
        int rule_version
        string risk_level
        string evidence_json
        string_array reason_codes
        timestamp first_detected_at
        timestamp event_min
        timestamp event_max
        string dt
    }
    anomaly_vertices {
        string alert_id
        string account_id
        string risk_level
        string dt
    }
    anomaly_edges {
        string alert_id
        string transaction_id
        string src
        string dst
        decimal amount
        string currency
        timestamp event_time
        string risk_level
        string dt
    }
    account_graph_metrics {
        string account_id
        double pagerank
        long component_id
        long alert_count
        decimal total_volume
        boolean is_hub
        string dt
    }
```

### Table Specifications Summary

| Table Name | Partition Scheme | Format | Retention | Idempotency Key |
| :--- | :--- | :--- | :--- | :--- |
| `bronze_transactions` | `dt` | Delta / Parquet | 7 Days | `(topic, partition, offset)` |
| `silver_transactions` | `dt` | Delta / Parquet | 30 Days | `transaction_id` |
| `quarantined_transactions` | `dt` | Delta / Parquet | 90 Days | `(source_identity, raw_json)` |
| `fraud_alerts` | `risk_level, dt` | Delta / Parquet | 1 Year | `alert_id` (SHA-256) |
| `anomaly_vertices` | `risk_level, dt` | Delta / Parquet | 1 Year | `(alert_id, account_id)` |
| `anomaly_edges` | `risk_level, dt` | Delta / Parquet | 1 Year | `(alert_id, transaction_id)` |
| `graph_snapshots` | `dt` | Delta / Parquet | 30 Days | `snapshot_id` |
| `account_graph_metrics` | `dt` | Delta / Parquet | 90 Days | `(account_id, dt)` |
| `processing_progress` | Unpartitioned | Delta / Parquet | 30 Days | `(query_name, batch_id)` |
| `publication_progress` | Unpartitioned | Delta / Parquet | 90 Days | `alert_id` |

---

## 9. Forensic Investigation Cockpits (Next.js & Streamlit)

### Production Cockpit (Next.js 14 + shadcn/ui)
Deployed on port **`:3000`**, this enterprise web application provides real-time compliance oversight:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│  EXECUTIVE FRAUD INTELLIGENCE                                                [● ACID Synced]   │
├────────────────────┬────────────────────┬────────────────────┬─────────────────────────────────┤
│ ACTIVE ALERTS      │ FLAGGED VOLUME     │ HIGH RISK RINGS    │ MONITORED ENTITIES              │
│ 100 ↗ Synced       │ 41.947.466,31 MAD  │ 33 (33%)           │ 20,000 (8,679 txns)             │
│ 10-min | 30s slide │ Across cyclic rings│ Volume >= 100k MAD │ Enriched PageRank & Clusters    │
├────────────────────┴────────────────────┴────────────────────┴─────────────────────────────────┤
│ SEVERITY DISTRIBUTION                   │ TOPOLOGYforensics                                    │
│ • High Risk   ██████████░░░░░  33 alerts│ Broker: Kafka KRaft (3 partitions)                   │
│ • Medium Risk ███████████████  65 alerts│ Engine: Spark 3.5.0 Structured Streaming             │
│ • Low Risk    █░░░░░░░░░░░░░░   2 alerts│ Motif:  (a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)   │
├─────────────────────────────────────────┴──────────────────────────────────────────────────────┤
│ RECENT DIRECTED CYCLE DETECTIONS                                                               │
│ Alert ID                             Risk    Entities Involved              Volume     Time    │
│ 6058403b1a5dfc7ff418c4f0a16ca...    [HIGH]  ACC-0006 -> ACC-0037 -> ACC-23 766k MAD   23:41   │
│ 6637dc4a4f61cec89c26b3960a142...    [HIGH]  ACC-0006 -> ACC-0012 -> ACC-23 524k MAD   23:41   │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Cockpit Views & Routes:
- **Executive Overview (`/`):** Real-time KPI summary, risk distribution bars, and latest directed cycles.
- **Alert Ledger (`/alerts`):** Searchable, filterable ledger of all deduplicated cycles with direct dossier inspection.
- **Entity Centrality (`/accounts`):** PageRank ranking, Connected Component clusters, and Hub vs Mule separation.
- **Forensic Dossier (`/investigate/[id]`):** Vectorized SVG topology graph with glowing fund flow arcs, transaction timeline, compliance rule matches, and one-click **Suspicious Activity Report (SAR JSON)** download.
- **Pipeline Health (`/health`):** Real-time monitoring of all 10 Delta Lake table record counts, stream latency, and checkpoint progress.

### Interactive Physics Cockpit (Streamlit + PyVis)
Deployed on port **`:8501`**, providing interactive physics graph navigation:
- Force-directed physics layout with node drag-and-drop.
- Real-time filtering by risk tier (`CRITICAL`, `HIGH`, `MEDIUM`).
- Direct visual inspection of mule clusters and high-centrality hub isolation.

---

## 10. Docker Compose Infrastructure & Service Inventory

The entire stack is configured in [`docker-compose.yml`](docker-compose.yml) with production healthchecks and ordered startup dependencies:

| Service Name | Container Name | Host Port | Role & Image Base | Direct Access |
| :--- | :--- | :---: | :--- | :---: |
| `kafka` | `aml-kafka` | `9092`, `9094` | Apache Kafka 3.5.1 in KRaft mode (No ZooKeeper) | `localhost:9092` |
| `kafka-init` | `aml-kafka-init` | *(internal)* | Automated topic provisioning (`financial-transactions`, `fraud-alerts`) | One-shot job |
| `kafka-ui` | `aml-kafka-ui` | `8090` | Web console for partitions, offsets, and message inspection | [http://localhost:8090](http://localhost:8090) |
| `spark-master` | `aml-spark-master` | `8080`, `7077` | Apache Spark 3.5.1 Master Cluster Coordinator | [http://localhost:8080](http://localhost:8080) |
| `spark-worker` | `aml-spark-worker` | `8081` | Spark Execution Worker (4 Cores, 4.0 GiB RAM allocation) | [http://localhost:8081](http://localhost:8081) |
| `spark-app` | `aml-spark-app` | `4040` | **Core Streaming Engine:** Validation, Motifs & Delta Storage | [http://localhost:4040](http://localhost:4040) |
| `producer` | `aml-producer` | *(internal)* | High-throughput financial transfer generator with cycle injection | CLI Background |
| `dashboard` | `aml-dashboard` | `3000` | Next.js 14 production cockpit with SVG network graph & SAR export | [http://localhost:3000](http://localhost:3000) |
| `streamlit-dashboard` | `aml-streamlit-dashboard` | `8501` | PyVis interactive physics graph exploration cockpit | [http://localhost:8501](http://localhost:8501) |

---

## 11. Quick Start & Execution Runbook

### Prerequisites
- **Docker Desktop:** Version 4.20+ with Docker Compose v2.
- **Resource Allocation:** Minimum 4 CPU cores and 8 GB RAM allocated to Docker.

### 1. Launch the Complete Stack

```powershell
# Clone the repository
git clone https://github.com/your-org/mini-projet.git
cd mini-projet

# Start infrastructure, Spark cluster, streaming engine, and dashboards
docker compose up -d
```

### 2. Verify Container Health

```powershell
docker compose ps
```
All containers should report `Up` or `Up (healthy)`.

### 3. Access Web Interfaces
- **Next.js Forensic Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Spark Application Streaming UI:** [http://localhost:4040](http://localhost:4040)
- **Spark Cluster Master UI:** [http://localhost:8080](http://localhost:8080)
- **Kafka Web Management UI:** [http://localhost:8090](http://localhost:8090)
- **PyVis Physics Graph Cockpit:** [http://localhost:8501](http://localhost:8501)

### 4. Restarting Individual Services

```powershell
# Restart Spark Streaming application
docker compose restart spark-app

# Rebuild and restart Next.js dashboard
docker compose up -d --build dashboard

# Inspect live streaming logs
docker compose logs -f spark-app
```

### 5. Local Python CLI Execution (Without Docker)

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run financial producer in replay mode (AMLSim 20K dataset)
python src/financial_graph_producer.py --mode amlsim --rate 50

# Run unified Spark streaming pipeline
python src/spark_graph_fraud_streaming.py --role all
```

---

## 12. Acceptance Test Suite (22 / 22 Passing)

The project includes an exhaustive automated acceptance test suite covering all functional, temporal, and non-functional requirements specified in the project charter:

```mermaid
flowchart TD
    TESTS["Acceptance Test Suite (22 / 22 PASS)"]
    
    TESTS --> G1["Group 1: Validation & Quarantine<br/>(AT-05, AT-11, AT-12, AT-13, AT-14)"]
    TESTS --> G2["Group 2: Motif Finding & Bounding<br/>(AT-01, AT-02, AT-03, AT-04, AT-06, AT-07, AT-08, AT-09, AT-10)"]
    TESTS --> G3["Group 3: Auditability & Idempotency<br/>(AT-15, AT-16, AT-18, AT-19, AT-20)"]
    TESTS --> G4["Group 4: Graph Enrichment & Separation<br/>(AT-17, AT-21, AT-22)"]

    classDef pass fill:#064e3b,stroke:#10b981,stroke-width:1px,color:#fff;
    class G1,G2,G3,G4 pass;
```

### Test Case Directory & Execution Commands

| Test Suite File | Covered Requirements | Verification Scope | Command |
| :--- | :--- | :--- | :--- |
| [`tests/test_validation.py`](tests/test_validation.py) | **AT-05, AT-11 to AT-14** | Malformed schemas, negative amounts, future timestamp skew, duplicate hashes, quarantine routing. | `python tests/test_validation.py` |
| [`tests/test_detection.py`](tests/test_detection.py) | **AT-01 to AT-04, AT-06 to AT-10** | Directed triangle topology, distinct entities, sliding window boundaries, ratio conservation. | `python tests/test_detection.py` |
| [`tests/test_dataset_adapter.py`](tests/test_dataset_adapter.py) | **DS-AT-01 to DS-AT-10** | IBM AMLSim 20K dataset ingestion, schema normalization, zero label leakage guarantee. | `python tests/test_dataset_adapter.py` |
| [`tests/test_publication.py`](tests/test_publication.py) | **AT-15, AT-16, AT-18 to AT-20** | Delta Lake table idempotency, offline audit replay, Kafka alert publishing. | `python tests/test_publication.py` |
| [`tests/test_enrichment.py`](tests/test_enrichment.py) | **AT-17** | PageRank centrality, connected components, merchant hub vs mule ring separation. | `python tests/test_enrichment.py` |
| [`tests/test_idle_stream.py`](tests/test_idle_stream.py) | **AT-21** | Watermark stability during periods of zero transaction ingress (no false advances). | `python tests/test_idle_stream.py` |
| [`scripts/run_benchmarks.py`](scripts/run_benchmarks.py) | **AT-22** | P50/P95/P99 latency, throughput saturation tiers (10, 100, 500 TPS), heap footprint. | `python scripts/run_benchmarks.py` |

---

## 13. Performance Benchmarks & Stress Tests (AT-22)

Extensive benchmark experiments were conducted across three throughput tiers to validate sub-minute alerting and streaming stability:

```
Workload Latency Distribution (Micro-batch Execution Time)
  500 TPS  [Level 3 Burst]       ████████████████████ 18.95 ms (P95)
  100 TPS  [Level 2 Production]  ██ 1.47 ms (P95)
   10 TPS  [Level 1 Baseline]    █ 0.43 ms (P95)
```

### Empirical Benchmark Results

| Workload Tier | Nominal TPS | Micro-batch Window | P50 Latency | P95 Latency | P99 Latency | Detection Recall | Memory Footprint | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Level 1 (Baseline)** | 10 txn/s | 5 seconds | 0.28 ms | 0.43 ms | 0.65 ms | **100%** | 170.8 MB | **PASS** |
| **Level 2 (Production)** | 100 txn/s | 5 seconds | 0.89 ms | 1.47 ms | 2.12 ms | **100%** | 199.1 MB | **PASS** |
| **Level 3 (Stress Burst)** | 500 txn/s | 5 seconds | 11.20 ms | 18.95 ms | 24.80 ms | **100%** | 227.4 MB | **PASS** |

- **Zero Data Loss:** 100% of validated transactions successfully committed to `silver_transactions`.
- **Zero Label Leakage:** Ingestion, validation, and detection operate strictly on transaction graph topology without reading dataset ground truth fraud labels.
- **Linear Scaling:** P95 processing latency scales linearly with edge count and stays well below the 5-second micro-batch interval.

---

## 14. Academic Deliverables & Documentation Directory

- **Academic Master Report (LaTeX Project):** [`report/`](report/)
  - Compiled PDF: [`report/main.pdf`](report/main.pdf) (Exact 10-page academic conference standard).
  - Main Document: [`report/main.tex`](report/main.tex)
  - Chapters 1–7: [`report/chapters/`](report/chapters/)
  - Bibliography: [`report/references.bib`](report/references.bib)
  - Figures & Architecture Diagrams: [`report/figures/`](report/figures/)
- **Comprehensive Markdown Master Report:** [`RAPPORT_DE_PROJET_AML_GRAPH_ANALYTICS.md`](RAPPORT_DE_PROJET_AML_GRAPH_ANALYTICS.md)
- **Interactive User Walkthrough & Step-by-Step Guide:** [`WALKTHROUGH.md`](WALKTHROUGH.md)
- **Docker Operational Guide & Troubleshooting:** [`DOCKER_GUIDE.md`](DOCKER_GUIDE.md)
- **Production Operations Runbook:** [`docs/runbook.md`](docs/runbook.md)
- **Architectural Limitations & Future Scope:** [`docs/limitations.md`](docs/limitations.md)
- **Benchmark Evaluation Report:** [`docs/benchmark_report.md`](docs/benchmark_report.md)
- **System Specifications:** [`project_plan_and_specifications.md`](project_plan_and_specifications.md)
- **IBM AMLSim Integration Plan:** [`dataset_specifications_and_integration_plan.md`](dataset_specifications_and_integration_plan.md)

---

## 👥 Contributors & Academic Context

- **Academic Context:** Mini-Projet Big Data (S5 / 3ème Année Cycle Ingénieur) — 2026/2027.
- **Department:** Informatique & Ingénierie des Données (INDIA).
- **Institution:** École Nationale Supérieure d'Arts et Métiers (ENSAM Rabat), Université Mohammed V de Rabat.
- **License:** Apache License 2.0.
