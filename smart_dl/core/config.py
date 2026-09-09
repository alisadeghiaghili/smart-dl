"""Configuration persistence — JSON file in APPDATA."""
from __future__ import annotations

import json
import os
from typing import Any

_SMARTDL_CONFIG: str = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "SmartDL", "config.json"
)


def _bak_path() -> str:
    return _SMARTDL_CONFIG + ".bak"


def load_config() -> dict[str, Any]:
    """Load config from disk.

    Falls back to the ``.bak`` copy if the primary file is missing or corrupt,
    so a bad write can never silently wipe the user's proxy/cookie-browser
    choice. Returns an empty dict only if neither file is readable.
    """
    try:
        with open(_SMARTDL_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        pass
    # Primary read failed (missing or corrupt) — try the last good backup.
    try:
        with open(_bak_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            from smart_dl.ui import warn
            warn("config.json was corrupt or missing — restored from backup.")
            return data
    except Exception:
        return {}


def save_config(data: dict[str, Any]) -> None:
    """Save config atomically: write a temp file, then ``os.replace`` into
    place, keeping a ``.bak`` of the previous contents. A crash mid-write can
    therefore no longer leave a truncated ``config.json``."""
    bak = _bak_path()
    tmp = _SMARTDL_CONFIG + ".tmp"
    try:
        os.makedirs(os.path.dirname(_SMARTDL_CONFIG), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # Roll the current file forward as the backup before swapping in the
        # new one, so we always have a known-good copy.
        if os.path.exists(_SMARTDL_CONFIG):
            try:
                os.replace(_SMARTDL_CONFIG, bak)
            except OSError:
                pass
        os.replace(tmp, _SMARTDL_CONFIG)
    except (PermissionError, OSError):
        # Best effort: clean up a leftover temp file, keep existing config.
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
