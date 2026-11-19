#!/usr/bin/env python3
"""
spark_graph_fraud_streaming.py — Root Convenience Launcher (Livrable 2/4)
Forwards execution to src/spark_graph_fraud_streaming.py.
"""
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import runpy
runpy.run_path(str(src_dir / "spark_graph_fraud_streaming.py"), run_name="__main__")
