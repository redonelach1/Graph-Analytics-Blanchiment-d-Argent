# 📖 AML GraphShield — Complete User Guide & Walkthrough

Welcome to the **AML GraphShield** operational walkthrough. This comprehensive guide provides step-by-step instructions to run, test, inspect, and benchmark the real-time Anti-Money Laundering (AML) Graph Analytics and Cycle Detection platform.

> 🎓 **Rapport Académique Officiel (LaTeX & Markdown) :**  
> Pour la documentation scientifique, théorique et formelle (conforme aux normes académiques de master / cycle d'ingénieur) :
> - **Projet LaTeX modulaire :** Répertoire [`report/`](report/) (compilable avec `pdflatex`, `latexmk` ou directement sur Overleaf via `report.zip`).
> - **Guide d'insertion des captures d'écran :** Consultez [`report/README.md`](report/README.md) pour remplacer les 15 placeholders d'images de `report/figures/` par vos propres captures.
> - **Rapport Markdown complet :** [`RAPPORT_DE_PROJET_AML_GRAPH_ANALYTICS.md`](RAPPORT_DE_PROJET_AML_GRAPH_ANALYTICS.md).

---

## 📑 Table of Contents

1. [Architecture & System Overview](#1-architecture--system-overview)
2. [Prerequisites & System Requirements](#2-prerequisites--system-requirements)
3. [Quick Start: Running with Docker Compose (Recommended)](#3-quick-start-running-with-docker-compose-recommended)
4. [Local Development Mode (Without Docker)](#4-local-development-mode-without-docker)
5. [Interactive UI Walkthrough (Next.js Dashboard)](#5-interactive-ui-walkthrough-nextjs-dashboard)
6. [Automated Testing Guide (22 Acceptance Tests)](#6-automated-testing-guide-22-acceptance-tests)
7. [Benchmark Suite & Performance Testing (AT-22)](#7-benchmark-suite--performance-testing-at-22)
8. [Live Demonstration Scenarios](#8-live-demonstration-scenarios)
9. [Troubleshooting & FAQ](#9-troubleshooting--faq)

---

## 1. Architecture & System Overview

AML GraphShield detects coordinated cyclic layering rings ($A \to B \to C \to A$) in real time.

```
                          ┌─────────────────────────────────────┐
                          │     Financial Graph Producer        │
                          │   (AMLSim 20K / Synthetic Mix)      │
                          └──────────────────┬──────────────────┘
                                             │ Kafka Topic: financial-transactions
                                             ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │ Apache Spark 3.5.0 Structured Streaming Engine                               │
 │                                                                              │
 │  1. Ingestion & Validation  ──► bronze_transactions ──► silver_transactions  │
 │                                                   └──► quarantined_txns      │
 │  2. Sliding Windowing       ──► 10-Minute Windows, 30s Slide, 120s Watermark │
 │  3. GraphFrames Motifs      ──► (a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)  │
 │  4. Idempotent Dedup        ──► SHA256 Canonical cycle_id & alert_id         │
 │  5. Offline Delta Store     ──► fraud_alerts, anomaly_edges, anomaly_vertices│
 │  6. Graph Enrichment        ──► PageRank (α=0.85), Connected Components      │
 └──────────────────────┬───────────────────────────────────────────────────────┘
                        │
          ┌─────────────┴───────────────┐
          ▼                             ▼
 ┌──────────────────┐        ┌──────────────────────────────────────────────┐
 │ Kafka Topic:     │        │ Next.js 14 + shadcn/ui Forensic Dashboard    │
 │ fraud-alerts     │        │ • Executive Overview & KPI Metrics           │
 │ (Downstream SAR) │        │ • Interactive Directed SVG Canvas Graph      │
 └──────────────────┘        │ • Account Centrality & Legitimate Hub (AT-17)│
                             │ • Suspicious Activity Report (SAR) JSON DL   │
                             └──────────────────────────────────────────────┘
```

---

## 2. Prerequisites & System Requirements

### Option A: Docker Deployment (Preferred)
- **Docker:** Engine 24.0+ and **Docker Compose** v2.20+
- **RAM:** Minimum 8 GB recommended (for Spark Master/Worker, Kafka broker, Next.js frontend).

### Option B: Local Host Development
- **Python:** 3.10, 3.11, or 3.12 (with pip).
- **Node.js:** v18.0.0+ or v20.0.0+ (with npm).
- **Java (optional for local PySpark execution):** OpenJDK 11 or 17.

---

## 3. Quick Start: Running with Docker Compose (Recommended)

The entire environment (KRaft Kafka, Kafka UI, Spark Master, Spark Worker, Spark Application, and Next.js Dashboard) is orchestrated via [`docker-compose.yml`](docker-compose.yml).

### Step 3.1: Build the Container Images
From the root repository directory:
```bash
docker compose build
```
This builds:
- The Spark 3.5 container preloaded with Delta Lake 3.3.0, GraphFrames 0.8.4, and Kafka connector JARs.
- The Next.js 14 Dashboard container with optimized standalone production build.

### Step 3.2: Launch the Services
```bash
docker compose up -d
```

### Step 3.3: Verify Service Status
Run `docker compose ps` to verify all services are running:
```text
NAME                       IMAGE                              STATUS          PORTS
mini-projet-kafka-1        confluentinc/cp-kafka:7.5.0        Up (healthy)    0.0.0.0:9092->9092/tcp
mini-projet-kafka-ui-1     provectuslabs/kafka-ui:latest      Up              0.0.0.0:8085->8080/tcp
mini-projet-spark-master-1 bitnami/spark:3.5.0                Up              0.0.0.0:7077->7077/tcp, 0.0.0.0:8080->8080/tcp
mini-projet-spark-worker-1 bitnami/spark:3.5.0                Up              0.0.0.0:8081->8081/tcp
mini-projet-spark-app-1    mini-projet-spark-app              Up              
mini-projet-dashboard-1    mini-projet-dashboard              Up              0.0.0.0:3000->3000/tcp
```

### Step 3.4: Access Web Consoles
Open your browser to:
- 🌐 **AML Next.js Dashboard:** [http://localhost:3000](http://localhost:3000)
- 📊 **Spark Master Web UI:** [http://localhost:8080](http://localhost:8080)
- 📬 **Kafka UI Topic Explorer:** [http://localhost:8085](http://localhost:8085)

### Step 3.5: Run Ingestion & Traffic Simulation
To generate transactions and stream them into the running pipeline:

```bash
# Replay official IBM AMLSim 20K dataset (with 200 injected cycle patterns)
docker compose exec spark-app python src/financial_graph_producer.py --mode amlsim --tps 50

# OR generate synthetic mixed traffic with real-time triangle injection
docker compose exec spark-app python src/financial_graph_producer.py --mode mixed --tps 20
```

### Step 3.6: Shutting Down the Stack
To stop all services and preserve Delta Lake data volumes:
```bash
docker compose down
```
To also purge stored volumes (clean reset):
```bash
docker compose down -v
```

---

## 4. Local Development Mode (Without Docker)

You can run individual components directly on your host machine.

### Step 4.1: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 4.2: Initialize Delta Lake Storage Schemas
```bash
python src/fraud_graph_delta_schema.py --init
```
This initializes all 10 Delta Lake schemas inside `data/delta/` and generates `data/delta/delta_schemas.sql`.

### Step 4.3: Run Financial Producer in Dry-Run Mode
Test the producer without requiring an active Kafka broker:
```bash
python src/financial_graph_producer.py --mode amlsim --dry-run
```

### Step 4.4: Launch the Next.js Investigation Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Step 4.5: Launch the Streamlit Fallback Dashboard (Alternative)
If you prefer a Python-only UI:
```bash
pip install streamlit
streamlit run src/graph_network_dashboard.py
```

---

## 5. Interactive UI Walkthrough (Next.js Dashboard)

The Next.js 14 frontend provides a forensic investigation cockpit designed for compliance officers and fraud analysts:

### 1. Executive Overview (`/`)
- **Key Metrics:** Real-time counters for active cycle alerts, flagged transaction volume in Moroccan Dirhams (`MAD`), and high-risk ratio percentage.
- **Sliding Window Banner:** Visual confirmation of the active $L=600s$ (10 min) window with $S=30s$ sliding cadence.
- **Recent Alert Feed:** Instant access to incoming detected rings.

### 2. Fraud Alerts Explorer (`/alerts`)
- **Risk Severity Filter:** Switch between `ALL`, `HIGH` ($\ge 100\text{k MAD}$ & balanced ratio), `MEDIUM` ($20\text{k}-100\text{k MAD}$), and `LOW`.
- **Search Bar:** Real-time search across Alert ID (`ALT-...`), Canonical Cycle Hash (`CYC-...`), or Account ID.
- **Sorting:** Sort cycles chronologically or by total flagged volume.
- **Actions:** Click **"Investigate"** on any row to open the forensic workbench.

### 3. Investigation Workbench (`/investigate/[id]`)
- **Directed Cycle Graph Canvas:** 
  - Dynamic SVG canvas displaying the 3-node ring topology ($A \to B \to C \to A$).
  - Animated pulsating risk halos and directional arrowheads.
  - Hover and click edge inspector: Click on any edge to highlight the transfer and display the transaction ID, exact amount, currency, and timestamp.
- **Account Dossier:** Displays PageRank scores, connected component cluster IDs, and prior alert counts for all implicated accounts.
- **Compliance Reason Codes:** Explanation tags (`DIRECTED_TRIANGLE`, `SAME_CURRENCY`, `HIGH_VALUE_THRESHOLD_MET`).
- **Transaction Timeline Table:** Step-by-step audit trail of each hop in the cycle.
- **Export SAR JSON:** Click **"Download SAR JSON"** to export an official Suspicious Activity Report dossier for FinCEN or regulatory authorities.

### 4. Account Centrality & Clustering (`/accounts`)
- Visualizes PageRank centrality distribution ($\alpha=0.85$, $10$ iterations).
- **AT-17 Hub Analysis:** Demonstrates that legitimate enterprise hubs (e.g., `ACC-MERCHANT-HUB` and `ACC-UTILITY-BILLING`) receive high PageRank centrality while remaining completely separate from fraudulent cycle alerts ($0$ false positives).

### 5. Pipeline Telemetry & Table Health (`/health`)
- Health status for Spark Structured Streaming and KRaft Kafka.
- Storage inspector displaying record counts and retention policies across all 10 Delta Lake tables.

---

## 6. Automated Testing Guide (22 Acceptance Tests)

The system includes a test suite covering 100% of the architectural acceptance criteria ($AT-01$ through $AT-22$) and dataset adapter tests ($DS-AT-01$ through $DS-AT-10$).

### Run All Acceptance Tests in One Command
```bash
python tests/test_validation.py; python tests/test_dataset_adapter.py; python tests/test_detection.py; python tests/test_publication.py; python tests/test_enrichment.py; python tests/test_idle_stream.py
```

### Individual Test Suites

| Suite | File | Acceptance Criteria Tested |
|:------|:-----|:---------------------------|
| **Validation & Quarantine** | [`tests/test_validation.py`](tests/test_validation.py) | **AT-05, AT-11, AT-12, AT-13, AT-14** (Malformed JSON, invalid decimals, duplicate payload handling, conflict quarantine, self-transfer exclusion, future timestamp tolerance). |
| **IBM AMLSim Adapter** | [`tests/test_dataset_adapter.py`](tests/test_dataset_adapter.py) | **DS-AT-01 to DS-AT-10** (Deterministic transaction hashing, timestamp delta preservation, strict zero label leakage). |
| **Temporal Motif Detection** | [`tests/test_detection.py`](tests/test_detection.py) | **AT-01 to AT-04, AT-06 to AT-10, AT-15, AT-16** (Known triangle detection, rotational start invariance, closing edge detection, open chain rejection, half-open $[start, end)$ window boundaries, overlapping window deduplication, out-of-order arrival, 4-node cycle rejection, currency homogeneity). |
| **Alert Publication & Recovery** | [`tests/test_publication.py`](tests/test_publication.py) | **AT-18, AT-19, AT-20** (Offline evidence graph reconstruction, idempotent Delta storage, Kafka publish-then-crash recovery). |
| **Graph Centrality Enrichment** | [`tests/test_enrichment.py`](tests/test_enrichment.py) | **AT-17** (Legitimate merchant hub gets top PageRank with 0 false fraud classifications, Connected Components clustering). |
| **Idle Stream Watermark** | [`tests/test_idle_stream.py`](tests/test_idle_stream.py) | **AT-21** (Watermark does not falsely advance due to wall-clock time during stream idle periods). |

Expected output:
```text
ALL TRANSACTION VALIDATION TESTS PASSED!
ALL DATASET ADAPTER ACCEPTANCE TESTS PASSED!
ALL TEMPORAL TRIANGLE DETECTION TESTS PASSED!
ALL PUBLICATION & PERSISTENCE ACCEPTANCE TESTS PASSED!
ALL ENRICHMENT ACCEPTANCE TESTS PASSED!
[PASS] AT-21: Idle stream watermark non-advancement verified successfully.
All idle stream tests passed!
```

---

## 7. Benchmark Suite & Performance Testing (AT-22)

To execute the performance benchmark suite fulfilling **Acceptance Test AT-22**:

```bash
python scripts/run_benchmarks.py
```

This runs three progressive load tiers:
1. **Level 1 (Smoke / Baseline):** 10 txn/s
2. **Level 2 (Standard Operating Profile):** 100 txn/s
3. **Level 3 (Peak / Stress Load):** 500 txn/s

### Expected Benchmark Output:
```text
--- Running Benchmark Level 1: 10 txn/s (Target: 100 txns) ---
--- Running Benchmark Level 2: 100 txn/s (Target: 500 txns) ---
--- Running Benchmark Level 3: 500 txn/s (Target: 1500 txns) ---

[PASS] Benchmark report successfully written to docs/benchmark_report.md
```

The script automatically writes the performance report to [`docs/benchmark_report.md`](docs/benchmark_report.md).

---

## 8. Live Demonstration Scenarios

### Scenario A: Injecting a Directed Cycle & Observing Detection
1. Start the Next.js Dashboard (`cd dashboard && npm run dev`).
2. Open [`http://localhost:3000/alerts`](http://localhost:3000/alerts).
3. In a terminal, run:
   ```bash
   python src/financial_graph_producer.py --mode triangle --tps 5
   ```
4. Observe the alert `ALT-7D29F4C1B039A8E2` appearing with `HIGH` risk level.
5. Click **"Investigate"** to view the directed triangular flow:
   $$\text{ACC-0081} \xrightarrow{\text{161,232.57 MAD}} \text{ACC-0014} \xrightarrow{\text{154,750.32 MAD}} \text{ACC-0003} \xrightarrow{\text{147,876.55 MAD}} \text{ACC-0081}$$

### Scenario B: Legitimate Hub vs. Mule Ring Separation (AT-17)
1. Navigate to [`http://localhost:3000/accounts`](http://localhost:3000/accounts).
2. Filter by **"Hubs"**:
   - `ACC-MERCHANT-HUB` has the highest PageRank score (`0.1428`) and high transaction volume ($1,250,000\text{ MAD}$).
   - Notice **Alert Count = 0**.
3. Filter by **"Mule Suspects"**:
   - Implicated accounts (`ACC-0081`, `ACC-0014`, `ACC-0003`) have lower PageRank scores (`0.0482`, `0.0451`, `0.0439`) but are correctly flagged with cycle alerts.
   - Proves the system does **not** rely on naive degree/volume heuristics, preventing costly false alarms on utility settlement accounts.

### Scenario C: Exporting a Suspicious Activity Report (SAR)
1. Open any alert dossier: [`http://localhost:3000/investigate/ALT-7D29F4C1B039A8E2`](http://localhost:3000/investigate/ALT-7D29F4C1B039A8E2).
2. Click **"Download SAR JSON"**.
3. Inspect the exported JSON file:
   - Contains the canonical SHA256 alert hash.
   - Contains the full edge evidence array and transaction IDs.
   - Reconstructed independently from Delta Lake without Kafka retention dependencies.

---

## 9. Troubleshooting & FAQ

### Q: Port 3000 or 9092 is already allocated on my machine.
- If port `3000` is taken, you can run the Next.js dashboard on another port:
  ```bash
  npm --prefix dashboard run dev -- -p 3001
  ```
- Or modify the host port binding in [`docker-compose.yml`](docker-compose.yml) (e.g. `"3001:3000"`).

### Q: Does the watermark advance when the transaction stream is paused?
- **No.** As tested and verified in **AT-21**, the watermark $W = H - 120s$ is strictly event-time driven. If no new transactions arrive, the watermark does not advance. Transactions arriving after an idle period are still accepted if their event time is within 120 seconds of the committed high-water mark.

### Q: Can GraphFrames checkpointing corrupt Spark Structured Streaming?
- **No.** The system enforces strict separation of checkpoint paths:
  - Streaming micro-batch offsets: `data/checkpoints/`
  - GraphFrames connected components scratch space: `data/graph_checkpoints/`

### Q: Where are the IBM AMLSim datasets located?
- Small smoke test dataset: `data/datasets/amlsim/smoke/` (30 accounts, 45 transactions).
- 20K cycle dataset: `data/datasets/amlsim/20K_cycle/20K_cycle200/` (20,000 accounts, 117,805 transactions, 200 injected cycle patterns).
- To re-download or update:
  ```bash
  python scripts/download_amlsim.py
  ```

---

*AML GraphShield — Built with Apache Spark, GraphFrames, Delta Lake, and Next.js.*

