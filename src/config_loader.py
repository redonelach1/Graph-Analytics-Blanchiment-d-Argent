"""
config_loader.py — Central configuration loader for Mini-Projet 17.

Loads YAML configuration from file path or APP_CONFIG_PATH environment variable,
merging defaults with any overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Priority:
    1. Explicit config_path argument
    2. APP_CONFIG_PATH environment variable
    3. Default path (config/default.yaml)
    """
    if config_path is None:
        config_path = os.environ.get("APP_CONFIG_PATH", str(DEFAULT_CONFIG_PATH))

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config

