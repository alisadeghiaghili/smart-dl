"""Configuration persistence — JSON file in APPDATA."""
from __future__ import annotations

import json
import os
from typing import Any

_SMARTDL_CONFIG: str = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "SmartDL", "config.json"
)


def load_config() -> dict[str, Any]:
    """Load config from disk. Returns empty dict on any error."""
    try:
        with open(_SMARTDL_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data: dict[str, Any]) -> None:
    """Save config to disk. Silently handles permission/filesystem errors."""
    try:
        os.makedirs(os.path.dirname(_SMARTDL_CONFIG), exist_ok=True)
        with open(_SMARTDL_CONFIG, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except PermissionError:
        pass
    except OSError:
        pass
