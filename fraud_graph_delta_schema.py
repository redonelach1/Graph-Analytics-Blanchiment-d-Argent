#!/usr/bin/env python3
"""
fraud_graph_delta_schema.py — Root Convenience Launcher (Livrable 3/4)
Forwards execution to src/fraud_graph_delta_schema.py.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import runpy
runpy.run_path(str(src_dir / "fraud_graph_delta_schema.py"), run_name="__main__")
