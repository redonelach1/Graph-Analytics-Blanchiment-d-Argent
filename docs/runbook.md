# 📘 AML GraphShield Operational Runbook

This document describes standard operating procedures, incident handling, disaster recovery, and operational maintenance for the Real-time AML Graph Analytics pipeline.

---

## 1. System Components & Service Ports

| Service | Port | Description | Health / Web Access |
|:--------|:----:|:------------|:----------------|
| **Next.js Dashboard** | `3000` | Analyst workbench & investigation GUI | `http://localhost:3000` (`/api/health`) |
| **Streamlit Dashboard** | `8501` | PyVis interactive graph console (Livrable 4) | `http://localhost:8501` |
| **Spark Master UI** | `8080` | Spark Cluster Master Web UI | `http://localhost:8080` |
| **Spark App UI** | `4040` | Live Spark Streaming DAG & micro-batch UI | `http://localhost:4040` |
| **Kafka Broker** | `9092` | KRaft event broker (external client port) | TCP `localhost:9092` |
| **Kafka UI** | `8090` | Topic, consumer group, and offset inspector | `http://localhost:8090` |

---

## 2. Standard Service Lifecycle

### 2.1 Starting the Stack
```bash
# Clean build and start all containers in detached mode
docker compose build
docker compose up -d

# Verify container statuses
docker compose ps
```

### 2.2 Verifying Topic Readiness
Check that both required Kafka topics are initialized:
```bash
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```
Required topics:
- `financial-transactions`: Transaction ingestion stream (3 partitions recommended)
- `fraud-alerts`: Emitted high/medium/low severity cycle alerts

---

## 3. Disaster Recovery & Troubleshooting

### 3.1 Spark Stream Stoppage & Crash Recovery
The pipeline persists all micro-batch offsets and state stores under:
- Structured Streaming Checkpoint: `data/checkpoints/`
- GraphFrames Connected Components Checkpoint: `data/graph_checkpoints/`

**Recovery Procedure:**
1. Stop the failing container or kill the background process.
2. Inspect logs: `docker compose logs spark-app --tail 200`
3. Restart the service without modifying the checkpoint directories. Spark Structured Streaming will resume from the exact last committed batch offset without dropping or duplicating transactions.

> [!CAUTION]
> Never delete `data/checkpoints` while in-flight transactions exist. Deleting this directory resets the Kafka consumer offset to `earliest` or `latest`.

### 3.2 Handling Checkpoint Directory Contamination
If a node crash occurs during a connected components execution:
- Note that `data/graph_checkpoints` is strictly separated from `data/checkpoints`.
- If the GraphFrames connected components checkpoint becomes corrupted, you may safely wipe `data/graph_checkpoints/*` while leaving `data/checkpoints` intact. GraphFrames will recreate its scratch graphs on the next enrichment interval.

### 3.3 Late-Arriving Event Troubleshooting
If transactions arrive with timestamps older than $W = H - 120s$:
- Check `quarantined_transactions` Delta table to see if transactions were flagged as expired or future events.
- Remember: Watermark advances **only** when higher event-time records arrive (AT-21). If the stream sits idle for hours, the watermark does **not** advance with wall-clock time.

---

## 4. SAR Regulatory Export Procedure

When compliance officers require a formal Suspicious Activity Report (SAR) for FinCEN or central banking authorities:
1. Navigate to the Next.js Dashboard: `http://localhost:3000/alerts`
2. Select the flagged alert row to enter the investigation view: `/investigate/[alert_id]`
3. Click **"Download SAR JSON"** on the top right action bar.
4. The downloaded dossier contains:
   - Canonical `alert_id` and `cycle_id` SHA256 hashes
   - Complete edge array with transaction IDs, source accounts, target accounts, timestamps, and currency amounts
   - Matching sliding window bounds $[start, end)$
   - Triggered reason codes and risk classification tier

