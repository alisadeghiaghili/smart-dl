"""Configuration persistence — atomic JSON load/save under the data directory."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from smart_dl.core.paths import get_config_path

__all__ = ["load_config", "save_config", "set_config_path_for_tests"]


_config_path_override: Path | None = None


def set_config_path_for_tests(path: Path | None) -> None:
    """Override the config file path (tests only).

    Parameters
    ----------
    path : pathlib.Path or None
        Absolute path to use, or ``None`` to restore the default.
    """
    global _config_path_override
    _config_path_override = Path(path) if path is not None else None


def _config_path() -> Path:
    if _config_path_override is not None:
        return _config_path_override
    return get_config_path()


def load_config() -> dict[str, Any]:
    """Load configuration from disk.

    Returns
    -------
    dict
        Parsed JSON object. Empty dict if the file is missing or invalid.
    """
    path = _config_path()
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def save_config(data: Mapping[str, Any]) -> bool:
    """Atomically persist configuration.

    Writes to a temporary file in the same directory, then ``os.replace``s
    onto the target so a crash cannot leave a truncated config.

    Parameters
    ----------
    data : Mapping[str, Any]
        JSON-serializable mapping.

    Returns
    -------
    bool
        ``True`` on success, ``False`` on I/O failure.
    """
    path = _config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(dict(data), indent=2, ensure_ascii=False)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent), prefix=".config-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        except OSError:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return True
    except OSError:
        return False
