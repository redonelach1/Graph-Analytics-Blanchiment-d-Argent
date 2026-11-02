# Mini-Projet 17 — Implementation Plan and Technical Specifications

## 0. Document purpose and status

This document defines what to implement, how the components interact, how to validate them, and in what order to deliver them.

Source requirement: Mini-Projet 17, “Graph Analytics & Blanchiment d’Argent.”

Terminology:
- MUST: required for the proposed baseline acceptance.
- SHOULD: recommended; deviation must be explained.
- OPTIONAL: outside the baseline.
- Proposed: an engineering decision to validate with the project supervisor, not a requirement copied from the brief.

The baseline uses synthetic data only. Alerts identify suspicious patterns; they do not establish money laundering.

## 1. Scope and decisions requiring approval

### 1.1 Requirements from the brief

| ID | Requirement |
|---|---|
| BR-01 | Ingest financial transfers continuously using Spark Structured Streaming. |
| BR-02 | Build a directed account/transfer graph. |
| BR-03 | Detect three-account closed cycles with GraphFrames motif finding. |
| BR-04 | Use a ten-minute sliding horizon and a two-minute watermark. |
| BR-05 | Compute PageRank and connected components. |
| BR-06 | Publish alerts to Kafka topic `fraud-alerts`. |
| BR-07 | Preserve anomaly subgraphs/topologies in Delta Lake, partitioned by risk level and date. |
| BR-08 | Provide a Streamlit/PyVis investigation interface. |
| BR-09 | Deliver the four named Python entry points. |
| BR-10 | Target sub-second alerting. |

### 1.2 Proposed baseline decisions

| Decision | Proposed resolution | Approval needed |
|---|---|---|
| Window interpretation | Explicit ten-minute windows, sliding every 30 seconds | Yes: brief omits slide interval |
| Alert timing | Provisional alerts on processing; do not wait for window finalization | Yes |
| Alert identity | One alert per rule version and transaction evidence set, independent of window | Yes |
| Currency handling | Baseline transactions in MAD; mixed-currency cycles excluded | Yes |
| Cycle semantics | Structural directed triangle within one window; chronological ordering not required | Yes |
| Graph metrics | Recompute every 60 seconds on the latest snapshot | Yes |
| Risk policy | LOW/MEDIUM/HIGH rule-based demonstration policy, not calibrated AML risk | Yes |
| Performance | Sub-second remains a target to benchmark, not a guaranteed capability | Yes |
| Deployment | Local Docker Compose first; distributed Spark validation if infrastructure exists | Yes |

A fixed sliding-window model is deliberately selected here instead of silently substituting a rolling ten-minute span rule. These models are not identical: some events spanning less than ten minutes may fail to share a particular aligned window near its boundary. The chosen semantics MUST be tested and documented.

### 1.3 Exclusions

Arbitrary-length cycle enumeration, production banking integration, ML/GNN models, currency conversion, automated account blocking, legal case management, Kubernetes, and proof of criminal activity are outside the baseline.

## 2. System architecture and responsibilities

```text
Synthetic producer
  → Kafka financial-transactions
  → ingestion query
      → Delta bronze_transactions
  → validation/acceptance worker
      → Delta silver_transactions
      → Delta quarantined_transactions
  → detection worker over accepted transactions + retained history
      → GraphFrames motif finding
      → Delta fraud_alerts (authoritative evidence/outbox payload)
  → Kafka publisher
      → Kafka fraud-alerts
      → publication progress

Periodic enrichment worker
  → recent silver transactions
  → PageRank / connected components
  → Delta graph_snapshots + account_graph_metrics

Dashboard
  → read-only Delta queries
  → bounded PyVis investigation graph
```

For the MVP these stages MAY share a process, but MUST preserve their separate responsibilities and recovery rules. No cross-table or Delta/Kafka atomic transaction is assumed.

| Component | Inputs | Outputs | Required behavior |
|---|---|---|---|
| Producer | Scenario configuration | Kafka events + separate truth manifest | Seeded, rate-controlled, observable delivery failures |
| Ingestion | Kafka records | Immutable raw Delta history | Preserve topic, partition, offset and original payload |
| Acceptance | Raw records | Canonical valid transactions / rejected records | Deterministic validation and identity decisions |
| Detection | Newly accepted transactions + relevant history | Alert rows with evidence | Correct across micro-batches and retries |
| Enrichment | Snapshot transaction range | Account metrics | Timestamped, independent of fast alerts |
| Publisher | Persisted alert payloads | Kafka events | Stable identity, retry-safe logical behavior |
| Dashboard | Alerts, metrics, transactions | Investigation UI | Read-only, bounded, freshness visible |

References: [R1], [R2], [R3], [R4].

## 3. Runtime and compatibility specification

### 3.1 Version selection

Proposed compatibility direction: Spark 3.5.x with Delta 3.3.x. Exact patch versions and a matching GraphFrames release MUST be selected and frozen in milestone M0. GraphFrames needs both the Python package and a matching Spark/Scala JVM artifact. Never rely on an unpinned `latest` installation.

Record exact Python, Java, Spark, Scala binary, Delta, GraphFrames Python/JVM, Kafka connector, Kafka broker image, Streamlit, and PyVis versions.

References: [R5], [R6].

### 3.2 Local deployment

Proposed services:
- Kafka broker in KRaft mode.
- Producer container.
- Spark application container(s).
- Dashboard container.
- Shared persistent volume for local Delta tables and checkpoints.

A single local broker with replication factor 1 is acceptable for demonstration, not a production durability design. All containers MUST use consistent internal Kafka advertised addresses. Host and container bootstrap addresses MUST be configured separately when needed.

Suggested development budget: 4–8 CPU cores and 16 GB RAM; this is an estimate to verify, not a measured minimum.

### 3.3 Environment acceptance test

MUST demonstrate:
1. Delta write/read.
2. Three-node GraphFrame construction.
3. Motif match.
4. PageRank.
5. Connected components.
6. Kafka source and sink.
7. Restart using persisted checkpoints.

Graph algorithm checkpoint paths MUST differ from streaming query checkpoint paths. [R7]

## 4. External data contracts

### 4.1 Input transaction JSON

```json
{
  "schema_version": 1,
  "transaction_id": "TXN-2026-8821",
  "source_account": "ACC-8812",
  "target_account": "ACC-4490",
  "montant": 45000.00,
  "devise": "MAD",
  "type_operation": "VIREMENT_COMMERCIAL",
  "timestamp": "2026-10-07T10:15:00Z"
}
```

| Field | Normalized name | Type | Validation |
|---|---|---|---|
| transaction_id | transaction_id | STRING | Required, nonempty |
| source_account | src | STRING | Required, nonempty |
| target_account | dst | STRING | Required, nonempty |
| montant | amount | DECIMAL(18,2) | Positive, in range; reject excess precision rather than silently rounding |
| devise | currency | STRING | Baseline MAD |
| type_operation | operation_type | STRING | Required supported value |
| timestamp | event_time | TIMESTAMP | Parseable ISO-8601 with timezone |
| schema_version | schema_version | INT | Default 1 for original brief-compatible payloads; reject unsupported versions |

Additional provenance fields: ingest_time, Kafka topic/partition/offset, raw payload, canonical payload hash, acceptance sequence or processing reference.

UTC MUST be used in Spark session configuration and persisted timestamps. Date partitions derive from UTC.

### 4.2 Validation outcomes

- VALID: canonical accepted transaction.
- INVALID: missing fields, malformed JSON, unsupported schema, invalid amount or timestamp.
- DUPLICATE: same transaction ID and same normalized business content; no new logical transaction.
- CONFLICT: same transaction ID with different business content; preserve original accepted record and quarantine conflicting input.
- SELF_TRANSFER: retain in history but exclude from distinct-account triangle matching.
- FUTURE_EVENT: reject when more than configured future skew ahead of ingestion time; proposed tolerance 60 seconds.

The canonical business-content hash MUST exclude arrival/provenance metadata. A single acceptance writer MUST serialize identity decisions. The accepted result MUST remain stable under retries.

### 4.3 Kafka contracts

| Topic | Key | Value | Local proposal |
|---|---|---|---|
| financial-transactions | source account | Input JSON | 3 partitions, replication 1 |
| fraud-alerts | alert_id | Alert JSON | 3 partitions, replication 1 |

Topic retention: proposed seven days for a local demo; configurable. No global ordering across partitions is assumed. Producer MUST observe delivery callbacks and flush on shutdown. [R2], [R8], [R9]

## 5. Temporal semantics and graph lifecycle

### 5.1 Explicit sliding windows

Window length L = 600 seconds; slide S = 30 seconds. Windows use UTC alignment and half-open membership:

```text
window_start <= event_time < window_end
```

A transaction participates in all aligned windows that contain its timestamp. This duplicates membership, not the logical transaction.

The streaming/window operator SHOULD use `withWatermark(event_time, "2 minutes")` with explicit window construction where supported. Custom GraphFrames processing MUST implement its own retained-history and finalization policy; a watermark annotation alone does not maintain a GraphFrame. [R1]

### 5.2 Lateness contract

Spark watermark guarantees are operator-dependent. Do not describe every event older than two minutes as automatically dropped by Spark.

For deterministic graph processing, persist an application event-time high-water mark H. Proposed policy:

1. Read previous committed H.
2. Classify new valid timestamps against W = H − 120 seconds.
3. Events older than W are retained but excluded from online graph updates and marked retrospective-only.
4. Eligible events update candidate windows.
5. Persist resulting alerts and evidence idempotently.
6. Advance H only after required detection outputs succeed.

Events exactly at W remain eligible under this policy. Classification uses the prior committed H; replay MUST reuse it. Excess future timestamps are rejected before advancing H.

This is an explicit application policy, not a claim that it exactly reproduces every Spark stateful operator's internal watermark behavior.

### 5.3 History and finalization

- Persist complete accepted history in Delta.
- For every newly eligible transaction, enumerate affected windows.
- Recover all accepted eligible transactions belonging to those windows.
- Run graph detection per affected window or an equivalent indexed computation.
- Require at least one newly accepted transaction in emitted candidates.
- A window can be finalized once the configured event-time watermark passes its end.
- In idle streams, event-time finalization may not advance; expose this in the UI.

Graph history reads MUST use explicit event-time bounds. Cleanup MUST NOT delete audit history required to reconstruct alerts.

## 6. Graph and detection specification

### 6.1 Graph schema

```text
Vertices: id STRING
Edges: src STRING, dst STRING, transaction_id STRING,
       amount DECIMAL(18,2), currency STRING, event_time TIMESTAMP
```

No orphan endpoint is permitted: vertices derive from the union of source and target accounts.

### 6.2 Triangle motif

```python
matches = graph.find(
    "(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)"
)
```

Mandatory filters:
- a, b, c have distinct account IDs.
- e1, e2, e3 have distinct transaction IDs.
- All edges belong to the same selected window.
- All edges have the same supported currency.
- No self-transfer edge.
- At least one edge is newly accepted for the current processing operation.

Do not aggregate away parallel transaction edges in the evidence graph. A separate deduplicated account-pair graph MAY be used for topology metrics.

Reference: [R3].

### 6.3 Canonical identities

```text
cycle_id = SHA256(canonical JSON array of sorted transaction IDs)
alert_id = SHA256(canonical JSON [rule_id, rule_version, cycle_id])
```

Canonical JSON MUST use a deterministic serialization. Window membership does not enter alert identity; the same evidence set matching overlapping windows produces one logical alert. Store earliest matching window or a bounded membership summary as explanatory metadata.

The identity scheme is scoped to this three-distinct-transaction rule, not arbitrary graph patterns.

### 6.4 Rule and risk policy

Rule ID: TEMPORAL_TRIANGLE. Version: 1.

All qualifying cycles produce an investigative alert. Proposed demonstration severity:
- HIGH: minimum edge amount ≥ configurable high-value threshold AND max/min amount ratio ≤ configured tolerance.
- MEDIUM: minimum edge amount ≥ configured medium threshold.
- LOW: other qualifying cycles.

Initial thresholds MUST be configuration values, explicitly labeled uncalibrated. PageRank MUST NOT be interpreted as a fraud probability. Alert explanation MUST include exact amounts, times, account IDs, transaction IDs, rule version and reason codes.

## 7. Enrichment specification

### 7.1 Snapshot

Every proposed 60 seconds, select the latest available completed detection snapshot or a clearly defined recent ten-minute interval. Store exact interval bounds, transaction count, vertex count, graph view and algorithm parameters.

Do not mix scores computed from different graph horizons without showing their provenance.

### 7.2 PageRank

Proposed initial parameters: resetProbability 0.15, maxIter 10. Values are experimental and MUST be benchmarked.

Output: snapshot_id, account_id, pagerank, computed_at, parameters.

Built-in PageRank MUST NOT be described as amount-weighted merely because edges carry an amount field. [R10]

### 7.3 Components

Run connected components on the declared topology snapshot. It groups connectivity without preserving a laundering interpretation. Strongly connected components are OPTIONAL.

Output: snapshot_id, account_id, component_id, computed_at.

Component IDs MUST NOT be used as permanent case identifiers. Configure graph checkpoints and unpersist retained algorithm results. [R7]

## 8. Storage specification

All schemas MUST be implemented in `fraud_graph_delta_schema.py` with a safe `--init` operation and documented migration policy.

| Table | Required fields | Logical identity | Partition proposal |
|---|---|---|---|
| bronze_transactions | raw_json, topic, partition, offset, ingest_time, dt | topic/partition/offset | dt |
| silver_transactions | transaction_id, src, dst, amount, currency, operation_type, event_time, ingest_time, payload_hash, online_eligible, dt | transaction_id | dt |
| quarantined_transactions | source identity, raw_json, reason_codes, recorded_at, dt | source identity/error category | dt |
| fraud_alerts | alert_id, cycle_id, rule_id, rule_version, risk_level, evidence JSON, reason_codes, first_detected_at, event_min/max, dt | alert_id | risk_level, dt |
| anomaly_vertices | alert_id, account_id, risk_level, dt | alert_id/account_id | risk_level, dt |
| anomaly_edges | alert_id, transaction_id, src, dst, amount, currency, event_time, risk_level, dt | alert_id/transaction_id | risk_level, dt |
| graph_snapshots | snapshot_id, graph_start/end, computed_at, counts, parameters | snapshot_id | dt |
| account_graph_metrics | snapshot_id, account_id, pagerank, component_id, computed_at | snapshot_id/account_id | dt |
| processing_progress | worker_id, source_position, high_water_mark, updated_at | worker_id | none |
| publication_progress | alert_id, published_at, attempt metadata | alert_id | optional dt |

Logical keys are enforced by application logic and idempotent merge; this table does not imply Delta automatically enforces primary-key uniqueness.

### 8.1 Authoritative alert and projections

The authoritative fraud_alerts row MUST contain enough embedded evidence to reconstruct the three-edge graph and the publication payload. Derived vertex/edge tables MAY be rebuilt from it. This avoids relying on an atomic write across separate Delta tables.

### 8.2 Idempotent recovery

- Raw ingestion preserves stable source identity.
- Accepted transaction writes use deterministic conflict policy and merge keys.
- Alert writes merge by alert_id and preserve original first_detected_at.
- Progress advances only after required outputs are durable.
- A crash before progress advancement causes replay; replay is harmless by identity.
- Use txnAppId/txnVersion only where their documented DataFrame-write semantics apply; do not assume they make arbitrary callbacks transactional.

References: [R4], [R11].

## 9. Alert publication specification

```json
{
  "schema_version": 1,
  "alert_id": "<stable hash>",
  "rule_id": "TEMPORAL_TRIANGLE",
  "rule_version": 1,
  "risk_level": "MEDIUM",
  "reason_codes": ["DIRECTED_TRIANGLE", "SAME_CURRENCY"],
  "account_ids": ["A", "B", "C"],
  "transaction_ids": ["T1", "T2", "T3"],
  "currency": "MAD",
  "event_time_min": "2026-10-07T10:10:00Z",
  "event_time_max": "2026-10-07T10:12:00Z",
  "first_detected_at": "<UTC timestamp>",
  "metrics_snapshot_id": null
}
```

Publication algorithm:
1. Select durable alert rows lacking publication progress.
2. Publish the exact stored payload with alert_id as Kafka key.
3. Wait for acknowledged delivery.
4. Record publication progress.

A crash between steps 3 and 4 may duplicate delivery. Consumers MUST deduplicate by alert_id. Kafka keys alone do not provide immediate consumer-side deduplication. The Spark Kafka sink documents at-least-once write semantics. [R2]

Optional enrichment updates require an explicit event version/update contract; they MUST NOT silently masquerade as a new initial alert.

## 10. Dashboard specification

The investigation dashboard is implemented as a modern **Next.js + shadcn/ui** application (with a Python Streamlit fallback):

| View | Required elements |
|---|---|
| Overview | KPI summary cards, severity distribution charts, processing freshness pulse |
| Alert list | Filterable table for date, risk, account, rule; stable alert ID; export |
| Investigation | Directed cycle graph with glowing risk edges, evidence table, timestamps, amounts, reason codes |
| Account profile | Associated alerts and latest timestamped PageRank/components metrics |
| Health | Pipeline telemetry: last successful batch, lag, errors, retrospective-only count |

Acceptance requirements:
- Modern Next.js 14+ interface utilizing shadcn/ui design system with dark/light themes.
- Highlight evidence edges separately from optional context with arrowheads and transaction-level tooltips.
- Default to the selected alert's small subgraph with zoom, pan, and node drag.
- Bound neighborhood expansion; proposed cap 300 nodes / 1,000 edges.
- Show when cached data and metrics were computed.
- Escape untrusted labels/HTML.
- Support offline demo assets where practical.
- Do not invoke global PageRank during page rendering.

## 11. Nonfunctional requirements and observability

| ID | Specification | Verification |
|---|---|---|
| NF-01 | No silent invalid-event loss | Reconcile raw records against accepted/duplicate/quarantine outcomes |
| NF-02 | Stable logical alerts under replay | Count distinct alert IDs before/after replay |
| NF-03 | Reconstruct each alert from persisted evidence | Load a historical alert without Kafka |
| NF-04 | Persist checkpoints outside ephemeral containers | Restart containers |
| NF-05 | No secrets committed | Repository scan; environment-based credentials |
| NF-06 | Synthetic identifiers only in demo | Review generator and fixtures |
| NF-07 | Configurable source rates, windows, thresholds, paths | Configuration validation tests |
| NF-08 | Bounded graph processing | Record active edges, motif candidates, batch durations |

Required structured log fields: worker, operation_id/batch_id, stage, duration_ms, input_count, accepted_count, rejected_count, alert_count, exception category.

Required metrics: Kafka lag, transactions/sec, active vertices/edges, motif candidates, late-event counts, batch duration, Delta write duration, publish duration, memory/shuffle indicators, alert latency p50/p95/p99.

## 12. Performance specification

Define alert latency as Kafka consumer observation time minus the producer delivery/arrival reference for the final required edge. Keep business event delay separate. Synchronize clocks or use one measurement host.

Proposed benchmark levels: 10, 100, then 500 transactions/sec; fixed-seed workloads with sparse, hub-heavy, parallel-edge and cycle-heavy variants. These are workload settings, not claimed capacities.

For each test record hardware, versions, trigger, window/slide, active graph size, input rate, run duration and warm-up.

BR-10 remains an explicit target: p95 initial-alert latency below one second under an agreed workload. Approval is required for the percentile/workload interpretation. A one-second trigger alone does not satisfy it. The architecture MUST report failure to meet this target rather than claiming it from configuration.

If graph processing cannot satisfy the target, document the measured limitation and propose a separate lightweight initial detection path with asynchronous GraphFrames verification. This is a change request, not a hidden replacement of the required architecture.

## 13. Verification and acceptance test matrix

| Test | Fixture/action | Pass criterion |
|---|---|---|
| AT-01 | Known triangle inside one window | Exactly one logical alert |
| AT-02 | Same triangle rotates vertex labels | Same alert_id |
| AT-03 | Edges arrive in three batches | Detection after final eligible edge |
| AT-04 | Open chain | No triangle alert |
| AT-05 | Repeated account/self-loop | Excluded from distinct-account rule |
| AT-06 | No common ten-minute window | No alert |
| AT-07 | Boundary events exactly at window end | Half-open membership respected |
| AT-08 | Same cycle matches overlapping windows | One logical alert |
| AT-09 | Eligible out-of-order final edge | Alert and correct evidence |
| AT-10 | Event older than application watermark | Retained, retrospective-only |
| AT-11 | Duplicate transaction | No new logical transaction or alert |
| AT-12 | Conflicting transaction payload | Original unchanged, conflict quarantined |
| AT-13 | Malformed JSON/invalid decimal | Quarantine, query continues |
| AT-14 | Future timestamp beyond tolerance | Rejected before event-time progress update |
| AT-15 | Mixed currencies | Excluded from baseline rule |
| AT-16 | Four-account cycle only | No three-account alert; documented scope |
| AT-17 | High-centrality legitimate hub | Metrics present, no unsupported fraud claim |
| AT-18 | Historical alert retrieval | Exact evidence reconstructed |
| AT-19 | Restart with persistent checkpoint | Processing resumes without logical duplicates |
| AT-20 | Kafka publish acknowledgement then crash | Possible redelivery; same alert identity |
| AT-21 | Idle stream | No false assumption of wall-clock finalization |
| AT-22 | Benchmark target | Measured result with workload and hardware |

Inject failures after raw persistence, accepted persistence, alert persistence, projection creation, Kafka acknowledgement, and before each progress commit.

For every failure test: record expected recovery, perform restart, reconcile counts, and save evidence.

## 14. Execution plan and dependencies

Assumption: one developer, six weeks. Effort estimates are planning estimates and require adjustment after environment setup.

| Work package | Estimate | Dependencies | Deliverables | Completion gate |
|---|---:|---|---|---|
| WP0 Requirements and architecture | 1–2 days | None | Approved decisions, contracts, diagrams | No unresolved temporal/latency semantics |
| WP1 Reproducible environment | 2–3 days | WP0 | Compose, locked dependencies, smoke script | All technology interoperability tests pass |
| WP2 Producer and truth fixtures | 2–3 days | WP1 | Generator, scenarios, manifest | Fixed-seed repeatability and delivery checks |
| WP3 Raw ingestion and acceptance | 3–4 days | WP2 | Bronze/silver/quarantine, identity handling | Validation/replay/conflict tests pass |
| WP4 Temporal graph detection | 4–5 days | WP3 | Window logic, history retrieval, motifs, identities | AT-01 through AT-16 pass |
| WP5 Durable alerts and publication | 3–4 days | WP4 | Authoritative evidence, projections, publisher | Failure/restart tests pass |
| WP6 Enrichment | 2 days | WP4 | PageRank/components snapshots | Known-graph tests and cleanup verified |
| WP7 Investigation UI | 2–3 days | WP5; WP6 for metrics | Streamlit/PyVis views | Historical alert investigation works |
| WP8 Benchmarks and handover | 3 days | WP5–WP7 | Results, runbook, demo, limitations | Reproducible delivery |

### Weekly milestones

- M0 / Week 1: approved specification and working stack.
- M1 / Week 2: deterministic generator and reliable accepted history.
- M2 / Week 3: temporal triangle detection across batches.
- M3 / Week 4: persisted explainable Kafka alerts and replay recovery.
- M4 / Week 5: enrichment and dashboard.
- M5 / Week 6: acceptance report, performance results and final demo.

Critical path: environment → accepted history → correct windows/history → motifs → durable alerts → publication recovery.

Dashboard mockups and fixture preparation can run in parallel if more people are available.

## 15. Required entry points and interfaces

```text
financial_graph_producer.py
  --config PATH --mode normal|triangle|mixed|replay --seed N --rate N

fraud_graph_delta_schema.py
  --config PATH --init
  # Destructive reset must be separate and explicitly confirmed.

spark_graph_fraud_streaming.py
  --config PATH --role ingest|accept|detect|enrich|publish|all

graph_network_dashboard.py
  # Run with streamlit run; load configuration from documented environment/path.
```

Supporting modules SHOULD separate validation, temporal policy, graph building, cycle identities, persistence, publication and metrics.

Configuration MUST include Kafka addresses/topics, table/checkpoint paths, window length/slide, lateness policy, future skew, supported currencies, risk thresholds, enrichment interval and UI limits.

## 16. Risk register

| Risk | Impact | Mitigation | Trigger for action |
|---|---|---|---|
| Spark/Delta/GraphFrames mismatch | Blocks development | Pin and smoke-test first | Any JVM/classpath failure |
| Window semantic ambiguity | Wrong acceptance behavior | Approve Section 5 before coding | Evaluator expects different model |
| Motif combinatorial growth | Latency/memory failure | Bounded windows, candidate metrics, load tests | Growing backlog or spill |
| Late data misses cycles | Incorrect detection | Affected-window recovery, boundary fixtures | AT-09/10 failure |
| Duplicate side effects | Misleading alert counts | Deterministic IDs and recovery protocol | Restart reconciliation mismatch |
| Sub-second target infeasible | Requirement unmet | Early benchmark and explicit change request | p95 above agreed target |
| UI overload | Unusable demo | Small evidence-first views | Browser latency or memory growth |
| Dataset label mismatch | Invalid evaluation | Controlled fixtures separate from broad labels | Unsupported accuracy claims |

## 17. Resources and implementation references

Links are implementation references, not a promise that mutable latest documentation matches the frozen runtime. After WP1, record version-specific pages where available.

| ID | Resource | Used for |
|---|---|---|
| R1 | [Spark Structured Streaming APIs](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) | Watermarks, windows, foreachBatch and query semantics |
| R2 | [Spark Kafka integration](https://spark.apache.org/docs/latest/streaming/structured-streaming-kafka-integration.html) | Kafka source options, sink contracts and at-least-once writes |
| R3 | [GraphFrames motif finding](https://graphframes.io/04-user-guide/04-motif-finding.html) | Triangle DSL and motif filters |
| R4 | [Delta streaming reads/writes](https://docs.delta.io/delta-streaming/) | Idempotent writes and streaming recovery |
| R5 | [Delta release compatibility](https://docs.delta.io/releases/) | Spark/Delta version selection |
| R6 | [GraphFrames installation](https://graphframes.io/02-quick-start/01-installation.html) | Python/JVM artifact and Scala compatibility |
| R7 | [GraphFrames traversals/connectivity](https://graphframes.io/04-user-guide/05-traversals.html) | Components, checkpoints and persistence |
| R8 | [Confluent Python client](https://docs.confluent.io/kafka-clients/python/current/overview.md) | Producer callbacks, delivery and configuration |
| R9 | [Confluent local quick start](https://docs.confluent.io/platform/current/get-started/platform-quickstart.html) | Docker broker networking and topic setup |
| R10 | [GraphFrames centrality](https://graphframes.io/04-user-guide/03-centralities.html) | PageRank API and parameters |
| R11 | [Delta merge/update](https://docs.delta.io/delta-update/) | Deterministic upserts and deduplication |
| R12 | [PyVis API](https://pyvis.readthedocs.io/en/latest/documentation.html) | Directed graphs and HTML output |
| R13 | [Streamlit caching](https://docs.streamlit.io/develop/concepts/architecture/caching) | TTL and bounded read caching |
| R14 | [IBM AMLSim](https://github.com/IBM/AMLSim) | Synthetic pattern-generation inspiration |
| R15 | [AMLSim example data](https://github.com/IBM/AMLSim/wiki/Download-Example-Data-Set) | Larger test graphs |
| R16 | [IBM AML-Data](https://github.com/IBM/AML-Data) | Synthetic labeled transactions |
| R17 | [AMLworld research](https://ar5iv.labs.arxiv.org/html/2306.16424) | Generator/dataset methodology and limitations |
| R18 | [GraphFrames Python API](https://graphframes.io/api/python/graphframes.html) | Exact signatures for selected release |

AMLSim has older dependency requirements: isolate it or consume exports rather than importing its environment into the project. Use controlled injected cycles for rule correctness. AMLworld/AML-Data labels may describe patterns outside triangle detection; do not equate their transaction labels with temporal-triangle ground truth.

## 18. Definition of done and handover

Delivery is complete only when:
- All approved requirements have implementation and test evidence.
- The four required entry points exist and are documented.
- One-command or clearly sequenced setup works from a clean environment.
- Fixed-seed generation and saved fixtures reproduce the demonstration.
- Cross-batch, late-event, duplicate, conflict and restart tests pass.
- An alert can be reconstructed from persisted evidence without Kafka.
- Kafka duplicate delivery limitations are documented.
- Dashboard freshness and graph-metric provenance are visible.
- Performance report states workload, hardware, versions and unmet targets.
- README, architecture, schemas, runbook, test report and limitations are included.

Final demo: normal traffic → three edges across separate batches → one stable alert → graph evidence → replay → restart → enrichment context → measured performance.
