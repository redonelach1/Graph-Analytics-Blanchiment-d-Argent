# 📊 Mini-Projet 17 — Progress Tracker

## Graph Analytics & Blanchiment d'Argent (Anti-Money Laundering)

> **Last updated:** 2026-11-02 20:34 UTC  
> **Overall status:** 🟡 In Progress  
> **Current phase:** Phase 6 — Enrichment Pipeline

---

## Quick Status Dashboard

| Phase | Description | Status | Start | End | Notes |
|:-----:|---|:------:|:-----:|:---:|-------|
| 0 | Requirements & Architecture | 🟢 Complete | 2026-11-01 | 2026-11-01 | Versions locked, config created |
| 1 | Reproducible Environment | 🟡 In Progress | 2026-11-01 | — | Docker infra created, ready for manual build |
| 2 | Producer & Truth Fixtures | 🟢 Complete | 2026-11-02 | 2026-11-02 | Producer, AMLSim adapter, and 7 fixtures ready |
| 3 | Raw Ingestion & Acceptance | 🟢 Complete | 2026-11-02 | 2026-11-02 | Delta schemas, validation engine, ingestion pipeline |
| 4 | Temporal Graph Detection | 🟢 Complete | 2026-11-02 | 2026-11-02 | Temporal windows, GraphFrames motifs, canonical alert IDs |
| 5 | Durable Alerts & Publication | 🟢 Complete | 2026-11-02 | 2026-11-02 | Delta persistence, Kafka alert publisher, evidence reconstruction |
| 6 | Enrichment Pipeline | 🟡 In Progress | 2026-11-02 | — | Periodic PageRank & connected components |
| 7 | Investigation Dashboard | 🔴 Not Started | — | — | |
| 8 | Benchmarks & Handover | 🔴 Not Started | — | — | |

**Legend:** 🔴 Not Started · 🟡 In Progress · 🟢 Complete · 🔵 Blocked · ⚪ Skipped

---

## Milestone Tracking

| Milestone | Target Week | Status | Completion Date | Gate Passed? |
|---|:---:|:------:|:---:|:---:|
| M0 — Approved spec + working stack | Week 1 | 🟡 | — | ❌ |
| M1 — Generator + accepted history | Week 2 | 🟢 | 2026-11-02 | ✅ |
| M2 — Triangle detection across batches | Week 3 | 🟢 | 2026-11-02 | ✅ |
| M3 — Durable alerts + replay recovery | Week 4 | 🟢 | 2026-11-02 | ✅ |
| M4 — Enrichment + dashboard | Week 5 | 🟡 | — | ❌ |
| M5 — Acceptance report + final demo | Week 6 | 🔴 | — | ❌ |

---

## Phase 0: Requirements & Architecture (Days 1–2)

### Tasks

- [x] Review and finalize project specifications
- [ ] Get supervisor approval on proposed baseline decisions
  - [x] Window interpretation (10-min, 30s slide)
  - [x] Alert timing (provisional on processing)
  - [x] Currency handling (MAD baseline)
  - [x] Cycle semantics (structural triangle)
  - [x] Graph metrics recompute interval (60s)
  - [x] Risk policy (LOW/MEDIUM/HIGH)
  - [x] Performance target interpretation
  - [x] Deployment (local Docker Compose)
- [x] Finalize and lock version matrix
- [x] Create architecture diagrams
- [x] Document temporal semantics decisions

### Notes
- Versions locked in `docker/spark/Dockerfile` and `requirements.txt`
- Config values encoded in `config/default.yaml`
- Architecture documented in `detailed_project_plan.md`
- Supervisor approval still needed on all "Proposed" decisions

---

## Phase 1: Reproducible Environment (Days 3–5)

### Tasks

- [x] Create `docker-compose.yml` with all services
  - [x] Kafka broker (KRaft mode)
  - [x] Spark application container(s)
  - [x] Dashboard container
  - [x] Shared persistent volume
- [x] Pin all dependency versions
  - [x] Spark 3.5.x exact patch
  - [x] Delta Lake 3.3.x exact version
  - [x] GraphFrames JVM + Python exact version
  - [x] Kafka connector version
  - [x] Python packages (requirements.txt)
- [ ] Pass environment acceptance tests
  - [ ] Delta write/read
  - [ ] 3-node GraphFrame construction
  - [ ] Motif match
  - [ ] PageRank
  - [ ] Connected components
  - [ ] Kafka source and sink
  - [ ] Checkpoint restart

### Notes
- `docker-compose.yml` created with 6 services (kafka, kafka-init, kafka-ui, spark-master, spark-worker, spark-app, dashboard)
- `docker/spark/Dockerfile` downloads Delta 3.3.0, GraphFrames 0.8.4, Kafka connector JARs
- `docker/spark/spark-defaults.conf` pre-configures UTC, AQE, Delta extensions
- `docker/dashboard/Dockerfile` sets up Streamlit + PyVis
- `scripts/smoke_test.py` ready to validate all 7 environment checks
- **Next step:** Run `docker compose build && docker compose up -d` then execute smoke test

---

## Phase 2: Producer & Truth Fixtures (Days 6–8)

### Tasks

- [x] Implement `financial_graph_producer.py`
  - [x] `--mode normal` (random transactions)
  - [x] `--mode triangle` (guaranteed cycles)
  - [x] `--mode mixed` (normal + injected cycles)
  - [x] `--mode replay` (from saved fixture)
  - [x] `--mode amlsim` (IBM AMLSim dataset stream)
  - [x] `--seed N` (deterministic)
  - [x] `--rate N` (rate control)
  - [x] `--config PATH` (configuration)
  - [x] `--dry-run` (stdout logging without requiring Kafka)
- [x] Create controlled test fixtures (`tests/fixtures/`)
  - [x] `triangle_simple.json`
  - [x] `open_chain.json`
  - [x] `self_loop.json`
  - [x] `boundary_events.json`
  - [x] `duplicate_txn.json`
  - [x] `conflict_txn.json`
  - [x] `mixed_currency.json`
- [x] Acquire and integrate IBM AMLSim dataset
  - [x] `scripts/download_amlsim.py`
  - [x] `data/datasets/amlsim/manifest.yaml`
  - [x] `src/dataset_adapter.py` (canonical contract, zero label leakage)
  - [x] Smoke dataset (100 accounts)
  - [x] 20K dataset with 200 injected cycle patterns (20,000 accounts, 117,805 txns)
- [x] Verify fixed-seed repeatability
- [x] Verify Kafka delivery callbacks & fallback to dry-run
- [x] Run dataset adapter test suite (`tests/test_dataset_adapter.py`)

### Notes
- IBM AMLSim dataset downloaded and parsed cleanly (`smoke` and `20K_cycle200`).
- Producer tested across all 5 modes (`normal`, `triangle`, `mixed`, `replay`, `amlsim`).
- All 5 dataset acceptance tests (`DS-AT-01`, `DS-AT-02`, `DS-AT-04`, `DS-AT-06`, `DS-AT-09`) passed.

---

## Phase 3: Raw Ingestion & Acceptance (Days 9–12)

### Tasks

- [x] Implement `fraud_graph_delta_schema.py`
  - [x] Define all 10 table schemas and partition strategies
  - [x] `--init` safe initialization of Delta directories & SQL DDL
  - [x] `--reset --force` destructive reset with safety check
  - [x] Output standalone `delta_schemas.sql`
- [x] Implement ingestion worker (`src/spark_graph_fraud_streaming.py --role ingest`)
  - [x] Kafka → bronze_transactions (immutable append)
  - [x] Preserve topic, partition, offset, raw payload, ingest_time, dt
- [x] Implement acceptance worker (`src/validation.py` + `spark_graph_fraud_streaming.py --role accept`)
  - [x] JSON parsing + strict ISO-8601 UTC timestamp parsing
  - [x] VALID → silver_transactions (`online_eligible = true`)
  - [x] INVALID → quarantined_transactions with reason codes
  - [x] DUPLICATE detection (same ID & content) → idempotently ignored
  - [x] CONFLICT detection (same ID, different content) → original kept, conflict quarantined
  - [x] SELF_TRANSFER handling (src == dst) → accepted, flagged `online_eligible = false`
  - [x] FUTURE_EVENT rejection (>60s tolerance) → quarantined
  - [x] Canonical payload hash (excludes provenance)
  - [x] Single-writer serialization
- [x] Test deterministic replay & validation edge cases (`tests/test_validation.py`)

### Notes
- Delta Lake table schemas and DDL initialized in `data/delta/delta_schemas.sql`.
- Ingestion and acceptance workers wired into `src/spark_graph_fraud_streaming.py`.
- Validation suite passes 100% of tests (`tests/test_validation.py`).

---

## Phase 4: Temporal Graph Detection (Days 13–17)

### Tasks

- [x] Implement temporal policy module (`src/temporal_policy.py`)
  - [x] Sliding window (L=600s, S=30s)
  - [x] Half-open membership [window_start <= event_time < window_end)
  - [x] Application high-water mark (H)
  - [x] Lateness classification (W = H − 120s)
- [x] Implement graph builder module (`src/graph_builder.py`)
  - [x] Vertices from union of src/dst (no orphan endpoints)
  - [x] Edges with full transaction metadata
  - [x] GraphFrames constructor helper
- [x] Implement `foreachBatch` detection worker (`src/detection.py` + `spark_graph_fraud_streaming.py --role detect`)
  - [x] Identify affected windows for new transactions
  - [x] Recover full history per window from silver_transactions
  - [x] Build GraphFrame per window
  - [x] Execute motif: `(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)`
  - [x] Apply mandatory filters (distinct accounts, distinct txns, same currency)
  - [x] Require at least one new edge
- [x] Implement cycle identity module (`src/cycle_identities.py`)
  - [x] `cycle_id = SHA256(sorted transaction IDs)`
  - [x] `alert_id = SHA256([rule_id, rule_version, cycle_id])`
  - [x] Deterministic canonical JSON serialization
- [x] Implement risk classification (HIGH/MEDIUM/LOW)
- [x] Pass acceptance tests (`tests/test_detection.py`)

### Notes
- Built pure Python & GraphFrames motif detection engines.
- Passed 11 acceptance tests in `test_detection.py` covering AT-01, AT-02, AT-03, AT-04, AT-06, AT-07, AT-08, AT-09, AT-10, AT-15, AT-16.
- Milestone M2 achieved!

---

## Phase 5: Durable Alerts & Publication (Days 18–21)

### Tasks

- [x] Implement alert persistence (`src/detection.py` + `spark_graph_fraud_streaming.py`)
  - [x] `fraud_alerts` table with authoritative evidence row
  - [x] `anomaly_vertices` projection
  - [x] `anomaly_edges` projection
  - [x] Authoritative evidence in fraud_alerts row (reconstructable without Kafka)
- [x] Implement Kafka publisher (`src/publication.py`)
  - [x] Select unpublished alerts
  - [x] Publish with alert_id as Kafka key
  - [x] Wait for delivery acknowledgment
  - [x] Record publication progress in `publication_progress` table
- [x] Implement idempotent recovery
  - [x] Progress advances only after outputs durable
  - [x] Replay is harmless by stable alert identity
  - [x] Alert merge preserves original first_detected_at
- [x] Pass failure/restart & publication tests (`tests/test_publication.py`)
  - [x] AT-18: Historical alert evidence reconstruction
  - [x] AT-19: Idempotent restart & replay
  - [x] AT-20: Publication acknowledgment & consumer deduplication

### Notes
- Full alert publication formatting per Section 9 specification implemented in `src/publication.py`.
- Publisher wired to Delta table `publication_progress` for at-least-once tracking.
- All 3 persistence/publication acceptance tests (AT-18, AT-19, AT-20) passed.

---

## Phase 6: Enrichment Pipeline (Days 22–23)

### Tasks

- [ ] Implement enrichment worker
  - [ ] Select latest 10-min snapshot
  - [ ] Build graph from snapshot
  - [ ] Run PageRank (resetProbability=0.15, maxIter=10)
  - [ ] Run connected components
  - [ ] Persist to `graph_snapshots` + `account_graph_metrics`
  - [ ] Store exact interval bounds + parameters
- [ ] Separate graph checkpoint directory from streaming checkpoints
- [ ] Unpersist retained algorithm results
- [ ] Schedule every 60 seconds
- [ ] Verify known-graph test results

### Notes
<!-- Add notes as you progress -->

---

## Phase 7: Investigation Dashboard (Days 24–26)

### Tasks

- [ ] Implement `graph_network_dashboard.py`
- [ ] Overview page
  - [ ] Alert counts
  - [ ] Severity distribution
  - [ ] Processing freshness indicator
- [ ] Alert list page
  - [ ] Filters: date, risk level, account, rule
  - [ ] Stable alert ID display
- [ ] Investigation page
  - [ ] Directed cycle graph (PyVis)
  - [ ] Evidence table (amounts, times, accounts, txn IDs)
  - [ ] Reason codes display
  - [ ] Evidence edges highlighted vs. context
- [ ] Account profile page
  - [ ] Associated alerts
  - [ ] Latest PageRank + component ID
  - [ ] Metrics computation timestamp
- [ ] Health page
  - [ ] Last successful batch
  - [ ] Lag metrics
  - [ ] Error counts
  - [ ] Retrospective-only event count
- [ ] Performance guardrails
  - [ ] Bound graph to 300 nodes / 1,000 edges
  - [ ] Cache TTL on Delta reads
  - [ ] Show data freshness
  - [ ] Escape untrusted labels

### Notes
<!-- Add notes as you progress -->

---

## Phase 8: Benchmarks & Handover (Days 27–29)

### Tasks

- [ ] Run performance benchmarks
  - [ ] L1: 10 txn/s
  - [ ] L2: 100 txn/s
  - [ ] L3: 500 txn/s
  - [ ] Record p50/p95/p99 latency
  - [ ] Record hardware + versions
  - [ ] Record active graph sizes
- [ ] Complete acceptance test suite
  - [ ] AT-01 through AT-22 all pass
- [ ] Dataset integration tests
  - [ ] DS-AT-01 through DS-AT-10 all pass
- [ ] Documentation
  - [ ] README.md
  - [ ] Architecture documentation
  - [ ] Schema documentation
  - [ ] Runbook (setup + operations)
  - [ ] Test report
  - [ ] Limitations document
  - [ ] Performance report
- [ ] Final demo preparation
  - [ ] Normal traffic → 3 edges → 1 alert → graph evidence
  - [ ] Replay → restart → enrichment → measured performance

### Notes
<!-- Add notes as you progress -->

---

## Acceptance Test Results

| ID | Test | Result | Date | Notes |
|:---:|---|:------:|:----:|-------|
| AT-01 | Known triangle inside one window | ✅ | 2026-11-02 | Exactly 1 alert produced with full evidence |
| AT-02 | Same triangle rotated vertex labels | ✅ | 2026-11-02 | Traversal start invariance produces identical alert_id |
| AT-03 | Edges arrive in three batches | ✅ | 2026-11-02 | Detection triggers immediately on arrival of closing edge |
| AT-04 | Open chain (no alert) | ✅ | 2026-11-02 | Linear unclosed chains produce 0 alerts |
| AT-05 | Repeated account / self-loop | ✅ | 2026-11-02 | Self-transfers retained but excluded from online triangles |
| AT-06 | No common 10-min window | ✅ | 2026-11-02 | Events spanning >10 min share no window and produce 0 alerts |
| AT-07 | Boundary events at window end | ✅ | 2026-11-02 | Half-open membership [start, end) respected |
| AT-08 | Same cycle overlapping windows | ✅ | 2026-11-02 | Deduplicated by stable alert_id across overlapping windows |
| AT-09 | Out-of-order final edge | ✅ | 2026-11-02 | In-window out-of-order arrival correctly detected |
| AT-10 | Event older than watermark | ✅ | 2026-11-02 | Event time < W (H - 120s) classified retrospective-only |
| AT-11 | Duplicate transaction | ✅ | 2026-11-02 | Identical payload idempotently ignored without duplicate entry |
| AT-12 | Conflicting payload | ✅ | 2026-11-02 | Same ID with different payload quarantined; original kept |
| AT-13 | Malformed JSON / invalid decimal | ✅ | 2026-11-02 | Syntax and decimal precision errors rejected & quarantined |
| AT-14 | Future timestamp beyond tolerance | ✅ | 2026-11-02 | Event timestamps >60s ahead rejected & quarantined |
| AT-15 | Mixed currencies in cycle | ✅ | 2026-11-02 | Multi-currency loops excluded from baseline detector |
| AT-16 | Four-account cycle only | ✅ | 2026-11-02 | Length-4 cycle correctly ignored by 3-account detector |
| AT-17 | High-centrality hub | ⬜ | — | |
| AT-18 | Historical alert retrieval | ✅ | 2026-11-02 | Evidence graph and transactions reconstructed without Kafka |
| AT-19 | Restart with checkpoint | ✅ | 2026-11-02 | Replay recovery retains stable alert identity & first_detected_at |
| AT-20 | Kafka publish then crash | ✅ | 2026-11-02 | Redelivery safety verified; consumers deduplicate by alert_id |
| AT-21 | Idle stream | ⬜ | — | |
| AT-22 | Benchmark target | ⬜ | — | |

**Legend:** ⬜ Not Run · ✅ Pass · ❌ Fail · ⏭️ Skipped

---

## Dataset Test Results

| ID | Test | Result | Date | Notes |
|:---:|---|:------:|:----:|-------|
| DS-AT-01 | Repeat adaptation → identical IDs | ✅ | 2026-11-02 | Deterministic SHA256 hashes match across repeat passes |
| DS-AT-02 | Repeated equal-content → distinct txns | ✅ | 2026-11-02 | Row ordinals guarantee distinct transaction IDs |
| DS-AT-03 | Same account at different banks → distinct | ⬜ | — | For multi-bank datasets |
| DS-AT-04 | Shifted-time replay preserves deltas | ✅ | 2026-11-02 | Exact delta timedelta verified |
| DS-AT-05 | Accelerated arrival → timestamps unchanged | ⬜ | — | Rate limiting test |
| DS-AT-06 | Labels absent from detector features | ✅ | 2026-11-02 | Zero fraud label leakage into detector payload |
| DS-AT-07 | No silent currency relabeling | ⬜ | — | Baseline MAD verification |
| DS-AT-08 | Complete pattern sampling retained | ⬜ | — | Evaluated during benchmark |
| DS-AT-09 | Smallest AMLSim ≠ guaranteed cycles | ✅ | 2026-11-02 | Smoke dataset loads cleanly without assuming cycles |
| DS-AT-10 | Original vs. compressed time separated | ⬜ | — | Demonstrations vs benchmarks |

---

## Blockers & Issues Log

| # | Date | Description | Severity | Status | Resolution |
|:-:|:----:|---|:--------:|:------:|------------|
| | | _No issues logged yet_ | | | |

<!-- 
To add a new issue:
| 1 | 2026-11-XX | Description here | 🔴 High / 🟡 Medium / 🟢 Low | Open / Resolved | How it was resolved |
-->

---

## Decision Log

| # | Date | Decision | Rationale | Approved By |
|:-:|:----:|----------|-----------|:-----------:|
| 1 | 2026-11-01 | Project plan created | Baseline for implementation | — |
| 2 | 2026-11-01 | Version matrix locked: Spark 3.5, Delta 3.3.0, GraphFrames 0.8.4-spark3.5, Scala 2.12 | Compatibility verified via online research | — |
| 3 | 2026-11-01 | Docker Compose with 6 services (KRaft Kafka, no Zookeeper) | Simpler setup, fewer containers | — |
| 4 | 2026-11-01 | Separate graph checkpoints from streaming checkpoints | GraphFrames connected components corrupts streaming state if shared | — |
| 5 | 2026-11-01 | All config values in `config/default.yaml` | Single source of truth, easy to change | — |
| 6 | 2026-11-02 | Selected IBM AMLSim as primary external dataset | Pre-generated 20K nodes with 200 injected cycle patterns (`20K_cycle200`) | — |
| 7 | 2026-11-02 | Ground truth separation in AMLSimAdapter | Ground truth labels kept in auxiliary metadata; strictly absent from streaming payload | — |
| 8 | 2026-11-02 | Delta schemas & DDL initialization | 10 tables defined with partition strategies; idempotent `--init` | — |
| 9 | 2026-11-02 | Deterministic business validation logic | Single-writer serialization, canonical payload hash, conflict quarantine | — |
| 10 | 2026-11-02 | Dual motif detection engine (GraphFrames + pure Python) | Allows fast unit testing & execution on all environments | — |
| 11 | 2026-11-02 | Canonical alert_id calculation | Hash of sorted transaction IDs avoids alert duplication across sliding windows | — |
| 12 | 2026-11-02 | Delta publication progress tracking | At-least-once Kafka publish with explicit progress recording into Delta | — |

---

## Weekly Notes

### Week 1 (Target: M0)
- ✅ Created detailed project plan (`detailed_project_plan.md`)
- ✅ Created progress tracker (`progress_tracker.md`)
- ✅ Locked version matrix (Spark 3.5 / Delta 3.3.0 / GraphFrames 0.8.4)
- ✅ Created full Docker infrastructure (docker-compose.yml + Dockerfiles)
- ✅ Created config file (`config/default.yaml`) with all parameters
- ✅ Created smoke test script (`scripts/smoke_test.py`)
- ✅ Created 4 placeholder entry points in `src/`
- ✅ Created `.gitignore`
- 🔲 Need to: `docker compose build` and run smoke test
- 🔲 Need to: Get supervisor approval on baseline decisions

### Week 2 (Target: M1)
_Not started yet._

### Week 3 (Target: M2)
_Not started yet._

### Week 4 (Target: M3)
_Not started yet._

### Week 5 (Target: M4)
_Not started yet._

### Week 6 (Target: M5)
_Not started yet._

