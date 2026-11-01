# 📊 Mini-Projet 17 — Progress Tracker

## Graph Analytics & Blanchiment d'Argent (Anti-Money Laundering)

> **Last updated:** 2026-11-01  
> **Overall status:** 🔴 Not Started  
> **Current phase:** Phase 0 — Requirements & Architecture

---

## Quick Status Dashboard

| Phase | Description | Status | Start | End | Notes |
|:-----:|---|:------:|:-----:|:---:|-------|
| 0 | Requirements & Architecture | 🔴 Not Started | — | — | |
| 1 | Reproducible Environment | 🔴 Not Started | — | — | |
| 2 | Producer & Truth Fixtures | 🔴 Not Started | — | — | |
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
| M0 — Approved spec + working stack | Week 1 | 🔴 | — | ❌ |
| M1 — Generator + accepted history | Week 2 | 🔴 | — | ❌ |
| M2 — Triangle detection across batches | Week 3 | 🔴 | — | ❌ |
| M3 — Durable alerts + replay recovery | Week 4 | 🔴 | — | ❌ |
| M4 — Enrichment + dashboard | Week 5 | 🔴 | — | ❌ |
| M5 — Acceptance report + final demo | Week 6 | 🔴 | — | ❌ |

---

## Phase 0: Requirements & Architecture (Days 1–2)

### Tasks

- [ ] Review and finalize project specifications
- [ ] Get supervisor approval on proposed baseline decisions
  - [ ] Window interpretation (10-min, 30s slide)
  - [ ] Alert timing (provisional on processing)
  - [ ] Currency handling (MAD baseline)
  - [ ] Cycle semantics (structural triangle)
  - [ ] Graph metrics recompute interval (60s)
  - [ ] Risk policy (LOW/MEDIUM/HIGH)
  - [ ] Performance target interpretation
  - [ ] Deployment (local Docker Compose)
- [ ] Finalize and lock version matrix
- [ ] Create architecture diagrams
- [ ] Document temporal semantics decisions

### Notes
<!-- Add notes as you progress -->

---

## Phase 1: Reproducible Environment (Days 3–5)

### Tasks

- [ ] Create `docker-compose.yml` with all services
  - [ ] Kafka broker (KRaft mode)
  - [ ] Spark application container(s)
  - [ ] Dashboard container
  - [ ] Shared persistent volume
- [ ] Pin all dependency versions
  - [ ] Spark 3.5.x exact patch
  - [ ] Delta Lake 3.3.x exact version
  - [ ] GraphFrames JVM + Python exact version
  - [ ] Kafka connector version
  - [ ] Python packages (requirements.txt)
- [ ] Pass environment acceptance tests
  - [ ] Delta write/read
  - [ ] 3-node GraphFrame construction
  - [ ] Motif match
  - [ ] PageRank
  - [ ] Connected components
  - [ ] Kafka source and sink
  - [ ] Checkpoint restart

### Notes
<!-- Add notes as you progress -->

---

## Phase 2: Producer & Truth Fixtures (Days 6–8)

### Tasks

- [ ] Implement `financial_graph_producer.py`
  - [ ] `--mode normal` (random transactions)
  - [ ] `--mode triangle` (guaranteed cycles)
  - [ ] `--mode mixed` (normal + injected cycles)
  - [ ] `--mode replay` (from saved fixture)
  - [ ] `--seed N` (deterministic)
  - [ ] `--rate N` (rate control)
  - [ ] `--config PATH` (configuration)
- [ ] Create controlled test fixtures
  - [ ] `triangle_simple.json`
  - [ ] `triangle_cross_batch.json`
  - [ ] `open_chain.json`
  - [ ] `self_loop.json`
  - [ ] `boundary_events.json`
  - [ ] `duplicate_txn.json`
  - [ ] `conflict_txn.json`
- [ ] Generate truth manifest for each scenario
- [ ] Verify fixed-seed repeatability
- [ ] Verify Kafka delivery callbacks

### Notes
<!-- Add notes as you progress -->

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
| DS-AT-01 | Repeat adaptation → identical IDs | ⬜ | — | |
| DS-AT-02 | Repeated equal-content → distinct txns | ⬜ | — | |
| DS-AT-03 | Same account at different banks → distinct | ⬜ | — | |
| DS-AT-04 | Shifted-time replay preserves deltas | ⬜ | — | |
| DS-AT-05 | Accelerated arrival → timestamps unchanged | ⬜ | — | |
| DS-AT-06 | Labels absent from detector features | ⬜ | — | |
| DS-AT-07 | No silent currency relabeling | ⬜ | — | |
| DS-AT-08 | Complete pattern sampling retained | ⬜ | — | |
| DS-AT-09 | Smallest AMLSim ≠ guaranteed cycles | ⬜ | — | |
| DS-AT-10 | Original vs. compressed time separated | ⬜ | — | |

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
| | | _Add decisions as they are made_ | | |

---

## Weekly Notes

### Week 1 (Target: M0)
<!-- 
- What was accomplished
- What problems were encountered
- What's planned for next week
-->
_Not started yet._

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

