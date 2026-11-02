# 📊 Mini-Projet 17 — Progress Tracker

## Graph Analytics & Blanchiment d'Argent (Anti-Money Laundering)

> **Last updated:** 2026-11-02 19:10 UTC  
> **Overall status:** 🟡 In Progress  
> **Current phase:** Phase 2 — Producer, Truth Fixtures & IBM AMLSim Integration

---

## Quick Status Dashboard

| Phase | Description | Status | Start | End | Notes |
|:-----:|---|:------:|:-----:|:---:|-------|
| 0 | Requirements & Architecture | 🟢 Complete | 2026-11-01 | 2026-11-01 | Versions locked, config created |
| 1 | Reproducible Environment | 🟡 In Progress | 2026-11-01 | — | Docker infra created, ready for manual build |
| 2 | Producer & Truth Fixtures | 🟢 Complete | 2026-11-02 | 2026-11-02 | Producer, AMLSim adapter, and 7 fixtures ready |
| 3 | Raw Ingestion & Acceptance | 🔴 Not Started | — | — | |
| 4 | Temporal Graph Detection | 🔴 Not Started | — | — | |
| 5 | Durable Alerts & Publication | 🔴 Not Started | — | — | |
| 6 | Enrichment Pipeline | 🔴 Not Started | — | — | |
| 7 | Investigation Dashboard | 🔴 Not Started | — | — | |
| 8 | Benchmarks & Handover | 🔴 Not Started | — | — | |

**Legend:** 🔴 Not Started · 🟡 In Progress · 🟢 Complete · 🔵 Blocked · ⚪ Skipped

---

## Milestone Tracking

| Milestone | Target Week | Status | Completion Date | Gate Passed? |
|---|:---:|:------:|:---:|:---:|
| M0 — Approved spec + working stack | Week 1 | 🟡 | — | ❌ |
| M1 — Generator + accepted history | Week 2 | 🟡 | — | ❌ |
| M2 — Triangle detection across batches | Week 3 | 🔴 | — | ❌ |
| M3 — Durable alerts + replay recovery | Week 4 | 🔴 | — | ❌ |
| M4 — Enrichment + dashboard | Week 5 | 🔴 | — | ❌ |
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

- [ ] Implement `fraud_graph_delta_schema.py`
  - [ ] Define all table schemas
  - [ ] `--init` safe initialization
  - [ ] Separate destructive reset (confirmed only)
- [ ] Implement ingestion worker
  - [ ] Kafka → bronze_transactions (immutable append)
  - [ ] Preserve topic/partition/offset/raw payload
- [ ] Implement acceptance worker
  - [ ] JSON parsing + schema validation
  - [ ] VALID → silver_transactions
  - [ ] INVALID → quarantined_transactions
  - [ ] DUPLICATE detection (same ID, same content)
  - [ ] CONFLICT detection (same ID, different content)
  - [ ] SELF_TRANSFER handling
  - [ ] FUTURE_EVENT rejection (>60s tolerance)
  - [ ] Canonical payload hash (excludes provenance)
  - [ ] Single-writer serialization
- [ ] Test deterministic replay
- [ ] Test validation edge cases

### Notes
<!-- Add notes as you progress -->

---

## Phase 4: Temporal Graph Detection (Days 13–17)

### Tasks

- [ ] Implement temporal policy module
  - [ ] Sliding window (L=600s, S=30s)
  - [ ] Half-open membership
  - [ ] Application high-water mark (H)
  - [ ] Lateness classification (W = H − 120s)
- [ ] Implement graph builder module
  - [ ] Vertices from union of src/dst
  - [ ] Edges with full transaction metadata
  - [ ] No orphan endpoints
- [ ] Implement `foreachBatch` detection worker
  - [ ] Identify affected windows for new transactions
  - [ ] Recover full history per window
  - [ ] Build GraphFrame per window
  - [ ] Execute motif: `(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)`
  - [ ] Apply mandatory filters (distinct accounts, distinct txns, same currency)
  - [ ] Require at least one new edge
- [ ] Implement cycle identity module
  - [ ] `cycle_id = SHA256(sorted transaction IDs)`
  - [ ] `alert_id = SHA256([rule_id, rule_version, cycle_id])`
  - [ ] Deterministic canonical JSON serialization
- [ ] Implement risk classification (HIGH/MEDIUM/LOW)
- [ ] Pass acceptance tests AT-01 through AT-16

### Notes
<!-- Add notes as you progress -->

---

## Phase 5: Durable Alerts & Publication (Days 18–21)

### Tasks

- [ ] Implement alert persistence
  - [ ] `fraud_alerts` table with idempotent MERGE
  - [ ] `anomaly_vertices` projection
  - [ ] `anomaly_edges` projection
  - [ ] Authoritative evidence in fraud_alerts row
- [ ] Implement Kafka publisher
  - [ ] Select unpublished alerts
  - [ ] Publish with alert_id as Kafka key
  - [ ] Wait for delivery acknowledgment
  - [ ] Record publication progress
- [ ] Implement idempotent recovery
  - [ ] Progress advances only after outputs durable
  - [ ] Replay is harmless by identity
  - [ ] Alert merge preserves original first_detected_at
- [ ] Pass failure/restart tests
  - [ ] Crash after raw persistence
  - [ ] Crash after accepted persistence
  - [ ] Crash after alert persistence
  - [ ] Crash after Kafka acknowledgment
  - [ ] Restart reconciliation

### Notes
<!-- Add notes as you progress -->

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
| AT-01 | Known triangle inside one window | ⬜ | — | |
| AT-02 | Same triangle rotated vertex labels | ⬜ | — | |
| AT-03 | Edges arrive in three batches | ⬜ | — | |
| AT-04 | Open chain (no alert) | ⬜ | — | |
| AT-05 | Repeated account / self-loop | ⬜ | — | |
| AT-06 | No common 10-min window | ⬜ | — | |
| AT-07 | Boundary events at window end | ⬜ | — | |
| AT-08 | Same cycle overlapping windows | ⬜ | — | |
| AT-09 | Out-of-order final edge | ⬜ | — | |
| AT-10 | Event older than watermark | ⬜ | — | |
| AT-11 | Duplicate transaction | ⬜ | — | |
| AT-12 | Conflicting payload | ⬜ | — | |
| AT-13 | Malformed JSON / invalid decimal | ⬜ | — | |
| AT-14 | Future timestamp beyond tolerance | ⬜ | — | |
| AT-15 | Mixed currencies in cycle | ⬜ | — | |
| AT-16 | Four-account cycle only | ⬜ | — | |
| AT-17 | High-centrality hub | ⬜ | — | |
| AT-18 | Historical alert retrieval | ⬜ | — | |
| AT-19 | Restart with checkpoint | ⬜ | — | |
| AT-20 | Kafka publish then crash | ⬜ | — | |
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

