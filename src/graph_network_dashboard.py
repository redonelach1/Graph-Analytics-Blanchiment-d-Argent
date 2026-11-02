#!/usr/bin/env python3
"""
graph_network_dashboard.py — Streamlit + Graph Investigation Fallback Dashboard

Provides an alternative Python-native interactive investigation console over Delta Lake
fraud alerts and graph metrics, complementing the Next.js production dashboard.

Usage:
    streamlit run src/graph_network_dashboard.py
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import streamlit as st
except ImportError:
    st = None

# Fallback dataset mirroring Phase 4/5 outputs
MOCK_ALERTS = [
    {
        "alert_id": "ALT-7D29F4C1B039A8E2",
        "cycle_id": "CYC-9B14E2F3A8C7",
        "rule_id": "TEMPORAL_TRIANGLE",
        "rule_version": 1,
        "risk_level": "HIGH",
        "reason_codes": ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "HIGH_VALUE_THRESHOLD_MET", "AMOUNT_RATIO_TOLERANT_1.08"],
        "account_ids": ["ACC-0081", "ACC-0014", "ACC-0003"],
        "transaction_ids": ["TXN-64CAB8C7BF32", "TXN-E7D6A14A8A5F", "TXN-B55D9821222B"],
        "currency": "MAD",
        "first_detected_at": "2026-11-02 19:08:16",
        "total_amount": 463859.44,
        "evidence": {
            "accounts": ["ACC-0081", "ACC-0014", "ACC-0003"],
            "edges": [
                {"transaction_id": "TXN-64CAB8C7BF32", "src": "ACC-0081", "dst": "ACC-0014", "amount": 161232.57, "currency": "MAD", "time": "2026-11-02T19:08:15Z"},
                {"transaction_id": "TXN-E7D6A14A8A5F", "src": "ACC-0014", "dst": "ACC-0003", "amount": 154750.32, "currency": "MAD", "time": "2026-11-02T19:09:11Z"},
                {"transaction_id": "TXN-B55D9821222B", "src": "ACC-0003", "dst": "ACC-0081", "amount": 147876.55, "currency": "MAD", "time": "2026-11-02T19:12:34Z"}
            ]
        }
    },
    {
        "alert_id": "ALT-5B81C40D9E12FA47",
        "cycle_id": "CYC-AML-20K-042",
        "rule_id": "TEMPORAL_TRIANGLE",
        "rule_version": 1,
        "risk_level": "HIGH",
        "reason_codes": ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "HIGH_VALUE_THRESHOLD_MET", "RAPID_DISPERSAL"],
        "account_ids": ["ACC-0105", "ACC-0312", "ACC-0789"],
        "transaction_ids": ["TXN-AML-0042A", "TXN-AML-0042B", "TXN-AML-0042C"],
        "currency": "MAD",
        "first_detected_at": "2026-11-02 16:30:15",
        "total_amount": 620000.00,
        "evidence": {
            "accounts": ["ACC-0105", "ACC-0312", "ACC-0789"],
            "edges": [
                {"transaction_id": "TXN-AML-0042A", "src": "ACC-0105", "dst": "ACC-0312", "amount": 215000.00, "currency": "MAD", "time": "2026-11-02T16:26:00Z"},
                {"transaction_id": "TXN-AML-0042B", "src": "ACC-0312", "dst": "ACC-0789", "amount": 205000.00, "currency": "MAD", "time": "2026-11-02T16:28:10Z"},
                {"transaction_id": "TXN-AML-0042C", "src": "ACC-0789", "dst": "ACC-0105", "amount": 200000.00, "currency": "MAD", "time": "2026-11-02T16:29:45Z"}
            ]
        }
    },
    {
        "alert_id": "ALT-3C89B102A4E7F912",
        "cycle_id": "CYC-4A29E8D102C3",
        "rule_id": "TEMPORAL_TRIANGLE",
        "rule_version": 1,
        "risk_level": "MEDIUM",
        "reason_codes": ["DIRECTED_TRIANGLE", "SAME_CURRENCY", "MEDIUM_VALUE_THRESHOLD_MET"],
        "account_ids": ["ACC-0012", "ACC-0045", "ACC-0089"],
        "transaction_ids": ["TXN-1A2B3C4D5E6F", "TXN-7G8H9I0J1K2L", "TXN-3M4N5O6P7Q8R"],
        "currency": "MAD",
        "first_detected_at": "2026-11-02 18:45:22",
        "total_amount": 87400.00,
        "evidence": {
            "accounts": ["ACC-0012", "ACC-0045", "ACC-0089"],
            "edges": [
                {"transaction_id": "TXN-1A2B3C4D5E6F", "src": "ACC-0012", "dst": "ACC-0045", "amount": 30000.00, "currency": "MAD", "time": "2026-11-02T18:41:00Z"},
                {"transaction_id": "TXN-7G8H9I0J1K2L", "src": "ACC-0045", "dst": "ACC-0089", "amount": 29000.00, "currency": "MAD", "time": "2026-11-02T18:42:45Z"},
                {"transaction_id": "TXN-3M4N5O6P7Q8R", "src": "ACC-0089", "dst": "ACC-0012", "amount": 28400.00, "currency": "MAD", "time": "2026-11-02T18:44:30Z"}
            ]
        }
    }
]

MOCK_METRICS = [
    {"account_id": "ACC-MERCHANT-HUB", "pagerank": 0.1428, "component_id": 1, "is_hub": True, "alert_count": 0, "volume": 1250000.0},
    {"account_id": "ACC-UTILITY-BILLING", "pagerank": 0.1105, "component_id": 1, "is_hub": True, "alert_count": 0, "volume": 980000.0},
    {"account_id": "ACC-0105", "pagerank": 0.0512, "component_id": 4, "is_hub": False, "alert_count": 1, "volume": 420000.0},
    {"account_id": "ACC-0081", "pagerank": 0.0482, "component_id": 2, "is_hub": False, "alert_count": 2, "volume": 320000.0},
    {"account_id": "ACC-0014", "pagerank": 0.0451, "component_id": 2, "is_hub": False, "alert_count": 1, "volume": 308000.0},
    {"account_id": "ACC-0003", "pagerank": 0.0439, "component_id": 2, "is_hub": False, "alert_count": 1, "volume": 295000.0},
]

def render_dashboard():
    if st is None:
        print("[ERROR] Streamlit is not installed in the current Python environment.")
        print("Please run the Next.js dashboard via 'npm --prefix dashboard dev' or install streamlit via 'pip install streamlit'.")
        return

    st.set_page_config(
        page_title="AML GraphShield Investigation Console",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🛡️ AML GraphShield — Real-time Cycle Investigation")
    st.caption("Temporal directed cycle detection across 10-minute sliding windows (Fallback Console)")

    # Sidebar
    st.sidebar.header("Investigation Controls")
    risk_filter = st.sidebar.selectbox("Filter Risk Level", ["ALL", "HIGH", "MEDIUM", "LOW"])
    alerts = MOCK_ALERTS if risk_filter == "ALL" else [a for a in MOCK_ALERTS if a["risk_level"] == risk_filter]

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Cycle Alerts", len(alerts))
    with col2:
        total_vol = sum(a.get("total_amount", 0) for a in alerts)
        st.metric("Flagged Volume", f"{total_vol:,.2f} MAD")
    with col3:
        high_risk = sum(1 for a in alerts if a["risk_level"] == "HIGH")
        st.metric("High Risk Rings", high_risk)
    with col4:
        st.metric("Spark Windowing", "10m / 30s slide")

    st.divider()

    # Main Workbench Tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Alert Forensics", "👥 Account Centrality (PageRank)", "📊 Telemetry"])

    with tab1:
        if not alerts:
            st.info("No alerts found matching filter.")
        else:
            alert_options = {f"{a['alert_id']} ({a['risk_level']} - {a.get('total_amount', 0):,.2f} MAD)": a for a in alerts}
            selected_label = st.selectbox("Select Alert Dossier to Inspect", list(alert_options.keys()))
            selected_alert = alert_options[selected_label]

            left_col, right_col = st.columns([1, 1])

            with left_col:
                st.subheader(f"Cycle Topology: {selected_alert['cycle_id']}")
                st.write(f"**Risk Level:** `{selected_alert['risk_level']}`")
                st.write(f"**Rule:** `{selected_alert['rule_id']}` (v{selected_alert['rule_version']})")
                st.write(f"**Detected:** `{selected_alert['first_detected_at']}`")
                st.write(f"**Reason Codes:**")
                for r in selected_alert["reason_codes"]:
                    st.badge = st.markdown(f"- ✅ `{r}`")

                # ASCII/Text Directed Graph Representation
                edges = selected_alert["evidence"]["edges"]
                st.markdown("#### Directed Cycle Path:")
                for i, edge in enumerate(edges):
                    st.code(f"Step {i+1}: ({edge['src']}) ──[{edge['amount']:,.2f} {edge['currency']}]──> ({edge['dst']}) [Txn: {edge['transaction_id']}]")

            with right_col:
                st.subheader("Suspicious Activity Report (SAR)")
                sar_json = json.dumps(selected_alert, indent=2)
                st.json(selected_alert["evidence"])
                st.download_button(
                    label="📥 Export SAR Regulatory JSON",
                    data=sar_json,
                    file_name=f"sar_{selected_alert['alert_id']}.json",
                    mime="application/json"
                )

    with tab2:
        st.subheader("Graph Centrality Distribution (AT-17 Hub Analysis)")
        st.markdown(
            "PageRank scores (`resetProbability=0.15`, `maxIter=10`) separate high-volume utility/merchant hubs "
            "from localized money mule cycles."
        )
        st.table(MOCK_METRICS)

    with tab3:
        st.subheader("Delta Lake & Streaming Pipeline Status")
        st.markdown("- **Engine**: Spark 3.5.0 + GraphFrames 0.8.4")
        st.markdown("- **Watermark**: 120s Event Horizon ($W = H - 120s$)")
        st.markdown("- **Delta Tables**: 10 tables initialized under `data/delta`")
        st.markdown("- **Kafka Bus**: KRaft broker (No Zookeeper required)")

if __name__ == "__main__":
    render_dashboard()
