# 🛡️ Real-Time AML Graph Analytics & Directed Cycle Detection

[![Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-orange?logo=apachespark)](https://spark.apache.org/)
[![Delta Lake](https://img.shields.io/badge/Delta%20Lake-3.3.0-blue?logo=delta)](https://delta.io/)
[![GraphFrames](https://img.shields.io/badge/GraphFrames-0.8.4-purple)](https://graphframes.github.io/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?logo=next.js)](https://nextjs.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-shadcn%2Fui-38bdf8?logo=tailwindcss)](https://ui.shadcn.com/)
[![Acceptance Tests](https://img.shields.io/badge/Tests-22%2F22%20PASS-brightgreen)](tests/)

An enterprise-grade, real-time Anti-Money Laundering (AML) streaming platform designed to detect complex cyclic fund-layering rings ($A \to B \to C \to A$) across continuous sliding windows with deterministic idempotency, sub-minute alerting, and zero label leakage.

---

## 🏛️ System Architecture

```
                                  ┌──────────────────────────────────────────────┐
                                  │            Financial Graph Producer          │
                                  │  --mode normal | triangle | mixed | amlsim   │
                                  └──────────────────────┬───────────────────────┘
                                                         │ Kafka Topic: financial-transactions
                                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Apache Spark 3.5.0 Structured Streaming Engine                                        │
│                                                                                        │
│  [1. Ingestion & Validation] ──► bronze_transactions ──► silver_transactions           │
│                                                     └──► quarantined_transactions     │
│                                                                                        │
│  [2. Temporal Windowing]      ──► 10-Min Sliding Window (30s slide), 120s Watermark    │
│                                                                                        │
│  [3. GraphFrames Motifs]      ──► (a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)         │
│                                                                                        │
│  [4. Idempotent Deduplication]──► SHA256 canonical cycle_id & alert_id                │
│                                                                                        │
│  [5. Offline Evidence Store]  ──► fraud_alerts, anomaly_edges, anomaly_vertices       │
│                                                                                        │
│  [6. Graph Enrichment]        ──► PageRank (resetProb=0.15), Connected Components      │
└──────────────────────┬─────────────────────────────────────────────────────────────────┘
                       │
         ┌─────────────┴───────────────┐
         ▼                             ▼
┌──────────────────┐       ┌─────────────────────────────────────────────────────────────┐
│ Kafka Topic:     │       │ Next.js 14 + shadcn/ui Forensic Investigation Dashboard     │
│ fraud-alerts     │       │ • Executive Overview & KPI Metrics                          │
│                  │       │ • Interactive SVG Network Graph with Glowing Arc Risk Paths │
│                  │       │ • Account Centrality & Clustering (Hub vs Mule Separation)  │
│                  │       │ • Suspicious Activity Report (SAR) JSON Dossier Export     │
└──────────────────┘       └─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Host Requirements
- **Python:** 3.10+ (with `pyyaml`, `pyspark`, `confluent-kafka`)
- **Node.js:** 18+ (for local Next.js frontend dev)
- **Docker & Docker Compose:** Installed and operational (production deployment)

### 2. Environment Configuration
Configuration settings are centralized in [`config/default.yaml`](config/default.yaml):
- Window Length: `600s` (10 minutes)
- Window Slide: `30s`
- Watermark Lag: `120s` (2 minutes behind committed high-water mark)
- Currencies: `["MAD"]`
- High-risk threshold: `100,000 MAD` (ratio tolerance `1.15`)

### 3. Running with Docker Compose
To start the entire end-to-end stack:
```bash
docker compose build
docker compose up -d
```

Services exposed:
- **Next.js Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Spark Master UI:** [http://localhost:8080](http://localhost:8080)
- **Kafka UI Console:** [http://localhost:8085](http://localhost:8085)
- **Kafka Broker (KRaft):** `localhost:9092`

---

## 💻 Local CLI Execution

### Running the Producer
```bash
# Replay IBM AMLSim 20K synthetic cycle dataset (117k txns, 200 cycle patterns)
python src/financial_graph_producer.py --mode amlsim --tps 50

# Synthetic streaming mix with injected triangles
python src/financial_graph_producer.py --mode mixed --tps 20
```

### Running the Spark Engine Roles
```bash
# Role 1: Ingestion & Validation
python src/spark_graph_fraud_streaming.py --role ingest

# Role 2: Temporal Triangle Detection
python src/spark_graph_fraud_streaming.py --role detect

# Role 3: Kafka Alert Publisher
python src/spark_graph_fraud_streaming.py --role publish

# Role 4: Graph Enrichment (PageRank & Connected Components)
python src/spark_graph_fraud_streaming.py --role enrich
```

### Running the Next.js Dashboard Locally
```bash
cd dashboard
npm install
npm run dev
# Open http://localhost:3000 in your browser
```

---

## 🧪 Acceptance Test Suite (22 / 22 Passing)

Execute the full automated test suite verifying all architectural requirements:

```bash
# Validation rules & quarantine logic (AT-05, AT-11, AT-12, AT-13, AT-14)
python tests/test_validation.py

# IBM AMLSim dataset adapter & zero label leakage (DS-AT-01 to DS-AT-10)
python tests/test_dataset_adapter.py

# GraphFrames motif matching & window boundaries (AT-01 to AT-04, AT-06 to AT-10, AT-15, AT-16)
python tests/test_detection.py

# Publication, offline reconstruction, and alert idempotency (AT-18, AT-19, AT-20)
python tests/test_publication.py

# Graph enrichment, PageRank, and Hub vs Mule separation (AT-17)
python tests/test_enrichment.py

# Idle stream watermark non-advancement (AT-21)
python tests/test_idle_stream.py

# Complete performance benchmarks (AT-22)
python scripts/run_benchmarks.py
```

---

## 📊 Benchmark Summary (AT-22)

| Workload Tier | Nominal TPS | Micro-batch P95 Latency | Detection Recall | Memory Footprint | Verdict |
|:--------------|:-----------:|:-----------------------:|:----------------:|:----------------:|:-------:|
| **Level 1 (Baseline)** | 10 txn/s | 0.43 ms | 100% | 170.8 MB | **PASS** |
| **Level 2 (Production)** | 100 txn/s | 1.47 ms | 100% | 199.1 MB | **PASS** |
| **Level 3 (Stress Burst)** | 500 txn/s | 18.95 ms | 100% | 227.4 MB | **PASS** |

See full report: [`docs/benchmark_report.md`](docs/benchmark_report.md).

---

## 📚 Technical Documentation
- [Operational Runbook & Recovery Guide](docs/runbook.md)
- [Architectural Constraints & Limitations](docs/limitations.md)
- [Acceptance Benchmark Report](docs/benchmark_report.md)
- [Full Project Specifications](project_plan_and_specifications.md)
- [IBM AMLSim Integration Plan](dataset_specifications_and_integration_plan.md)

