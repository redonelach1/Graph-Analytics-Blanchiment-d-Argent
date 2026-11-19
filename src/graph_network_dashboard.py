#!/usr/bin/env python3
"""
graph_network_dashboard.py — Streamlit + PyVis Graph Investigation Console

Entry point 4/4 of Mini-Projet 17 (Livrables Ingénieur).
Provides an interactive graph visualization console with PyVis and Streamlit,
complementing the production Next.js 14 web dashboard.

Usage:
    streamlit run src/graph_network_dashboard.py
    python src/graph_network_dashboard.py --export-html
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("graph_network_dashboard")

try:
    import streamlit as st
    import streamlit.components.v1 as components
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    components = None
    STREAMLIT_AVAILABLE = False

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    Network = None
    PYVIS_AVAILABLE = False


# Reference Alerts Dataset
MOCK_ALERTS: List[Dict[str, Any]] = [
    {
        "alert_id": "ALT-7D29F4C1B039A8E2",
        "cycle_id": "CYC-9B14E2F3A8C7",
        "rule_id": "TEMPORAL_TRIANGLE",
        "rule_version": 1,
        "risk_level": "CRITICAL",
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

MOCK_METRICS: List[Dict[str, Any]] = [
    {"account_id": "ACC-MERCHANT-HUB", "pagerank": 0.1428, "component_id": 1, "is_hub": True, "alert_count": 0, "volume": 1250000.0},
    {"account_id": "ACC-UTILITY-BILLING", "pagerank": 0.1105, "component_id": 1, "is_hub": True, "alert_count": 0, "volume": 980000.0},
    {"account_id": "ACC-0105", "pagerank": 0.0512, "component_id": 4, "is_hub": False, "alert_count": 1, "volume": 420000.0},
    {"account_id": "ACC-0081", "pagerank": 0.0482, "component_id": 2, "is_hub": False, "alert_count": 2, "volume": 320000.0},
    {"account_id": "ACC-0014", "pagerank": 0.0451, "component_id": 2, "is_hub": False, "alert_count": 1, "volume": 308000.0},
    {"account_id": "ACC-0003", "pagerank": 0.0439, "component_id": 2, "is_hub": False, "alert_count": 1, "volume": 295000.0},
]


def generate_interactive_network_html(alert: Dict[str, Any]) -> str:
    """Generates an interactive PyVis / Vis.js directed graph visualization HTML."""
    evidence = alert.get("evidence", {})
    accounts = evidence.get("accounts", [])
    edges = evidence.get("edges", [])

    if PYVIS_AVAILABLE:
        net = Network(height="460px", width="100%", directed=True, bgcolor="#0f172a", font_color="#f8fafc")
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=160, spring_strength=0.05)

        for acc in accounts:
            net.add_node(
                acc,
                label=acc,
                title=f"Compte: {acc}\nRôle: Nœud du Cycle",
                color={"background": "#0284c7", "border": "#38bdf8", "highlight": {"background": "#ef4444", "border": "#f87171"}},
                shape="dot",
                size=24,
                font={"color": "#f8fafc", "size": 14, "face": "monospace"}
            )

        for edge in edges:
            label = f"{edge['amount']:,.2f} {edge['currency']}"
            title = f"Txn: {edge['transaction_id']}\nMontant: {label}\nDate: {edge['time']}"
            net.add_edge(
                edge["src"],
                edge["dst"],
                label=label,
                title=title,
                arrows="to",
                color={"color": "#e11d48", "highlight": "#fb7185"},
                width=2.5,
                font={"color": "#fda4af", "size": 11, "align": "top"}
            )
        return net.generate_html()

    # Fallback to direct Vis.js template
    nodes_js = [{"id": acc, "label": acc, "shape": "dot", "size": 24, "color": {"background": "#0284c7", "border": "#38bdf8"}} for acc in accounts]
    edges_js = [
        {"from": e["src"], "to": e["dst"], "label": f"{e['amount']:,.0f} MAD", "arrows": "to", "color": "#e11d48", "font": {"color": "#fda4af", "size": 11}}
        for e in edges
    ]

    return f"""<!DOCTYPE html>
<html>
<head>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ margin: 0; background: #0f172a; font-family: sans-serif; }}
        #network {{ width: 100%; height: 460px; }}
    </style>
</head>
<body>
    <div id="network"></div>
    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(nodes_js)});
        var edges = new vis.DataSet({json.dumps(edges_js)});
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            physics: {{ barnesHut: {{ springLength: 140, gravity: -2500 }} }},
            nodes: {{ font: {{ color: '#f8fafc' }} }},
            edges: {{ font: {{ align: 'top' }} }}
        }};
        new vis.Network(container, data, options);
    </script>
</body>
</html>"""


def render_dashboard():
    """Renders the Streamlit investigation dashboard."""
    if not STREAMLIT_AVAILABLE:
        print("[INFO] graph_network_dashboard.py is available as Livrable 4/4.")
        print("[INFO] To run the interactive web GUI: pip install streamlit pyvis && streamlit run src/graph_network_dashboard.py")
        print("[INFO] A production-grade Next.js 14 dashboard is also operational in dashboard/ (port 3000).")
        return

    st.set_page_config(
        page_title="AML GraphShield — Console d'Investigation",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🛡️ AML GraphShield — Navigation Visuelle des Graphes")
    st.caption("Livrable Ingénieur 4/4 : Interface interactive PyVis / Streamlit de détection de cycles AML")

    st.sidebar.header("Filtres d'Investigation")
    risk_filter = st.sidebar.selectbox("Niveau de Risque", ["TOUS", "CRITICAL", "HIGH", "MEDIUM"])
    filtered_alerts = MOCK_ALERTS if risk_filter == "TOUS" else [a for a in MOCK_ALERTS if a["risk_level"] == risk_filter]

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Alertes Actives", len(filtered_alerts))
    with c2:
        total_vol = sum(a.get("total_amount", 0) for a in filtered_alerts)
        st.metric("Volume Suspect", f"{total_vol:,.2f} MAD")
    with c3:
        crit_count = sum(1 for a in filtered_alerts if a["risk_level"] in ("CRITICAL", "HIGH"))
        st.metric("Cycles Critiques", crit_count)
    with c4:
        st.metric("Moteur Streaming", "Spark 10m / 30s")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🔍 Investigation Visuelle (PyVis)", "📈 Centralité PageRank (AT-17)", "⚙️ Télémétrie"])

    with tab1:
        if not filtered_alerts:
            st.info("Aucune alerte correspondant au filtre.")
        else:
            alert_map = {f"{a['alert_id']} ({a['risk_level']} - {a['total_amount']:,.2f} MAD)": a for a in filtered_alerts}
            chosen_key = st.selectbox("Sélectionner le dossier d'alerte :", list(alert_map.keys()))
            alert = alert_map[chosen_key]

            col_left, col_right = st.columns([1.2, 1])

            with col_left:
                st.subheader("Topologie Interactive du Cycle")
                html_code = generate_interactive_network_html(alert)
                components.html(html_code, height=480)

            with col_right:
                st.subheader(f"Dossier Réglementaire SAR : {alert['alert_id']}")
                st.write(f"**Identifiant du Cycle :** `{alert['cycle_id']}`")
                st.write(f"**Règle :** `{alert['rule_id']}` (v{alert['rule_version']})")
                st.write(f"**Montant Blanchi Total :** `{alert['total_amount']:,.2f} {alert['currency']}`")
                st.write("**Codes de Motif :**")
                for r in alert["reason_codes"]:
                    st.markdown(f"- ✅ `{r}`")

                st.download_button(
                    label="📥 Télécharger SAR JSON (Déclaration de Soupçon)",
                    data=json.dumps(alert, indent=2),
                    file_name=f"sar_{alert['alert_id']}.json",
                    mime="application/json"
                )

    with tab2:
        st.subheader("Isolation des Carrefours Marchands (PageRank AT-17)")
        st.markdown(r"Les comptes marchands à fort trafic ont un score PageRank élevé ($PR \gg 1/|V|$) qui les discrimine des mules criminelles.")
        st.table(MOCK_METRICS)

    with tab3:
        st.subheader("État du Système Lakehouse & Streaming")
        st.markdown("- **Moteur** : Apache Spark Structured Streaming 3.5.1 + GraphFrames 0.8.4")
        st.markdown("- **Bus Kafka** : Mode KRaft (sans ZooKeeper)")
        st.markdown("- **Couche Stockage** : 10 Tables Delta Lake sous `data/delta`")
        st.markdown("- **Interface Production** : Next.js 14 App Router (port 3000)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AML Graph Network Dashboard (PyVis / Streamlit)")
    parser.add_argument("--export-html", action="store_true", help="Export standalone interactive HTML visualization")
    args = parser.parse_args()

    if args.export_html:
        html = generate_interactive_network_html(MOCK_ALERTS[0])
        out_file = Path("docs/graph_network_visualization.html")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding="utf-8")
        print(f"[SUCCESS] Standalone PyVis HTML graph exported to {out_file.resolve()}")
    else:
        render_dashboard()
