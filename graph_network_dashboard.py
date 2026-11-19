#!/usr/bin/env python3
"""
graph_network_dashboard.py — Root Convenience Launcher for Livrable 4/4

Forwards execution to src/graph_network_dashboard.py.
Usage:
    streamlit run graph_network_dashboard.py
    python graph_network_dashboard.py --export-html
"""

import os
import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from graph_network_dashboard import render_dashboard, generate_interactive_network_html, MOCK_ALERTS

if __name__ == "__main__":
    import argparse
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
