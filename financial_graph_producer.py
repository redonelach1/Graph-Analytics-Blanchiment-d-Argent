#!/usr/bin/env python3
"""
financial_graph_producer.py — Root Convenience Launcher (Livrable 1/4)
Forwards execution to src/financial_graph_producer.py.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import runpy
runpy.run_path(str(src_dir / "financial_graph_producer.py"), run_name="__main__")
