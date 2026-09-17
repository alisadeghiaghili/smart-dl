"""Portable config import/export with secret scrubbing (roadmap R8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Set

__all__ = [
    "EXPORTABLE_KEYS",
    "SECRET_KEY_HINTS",
    "export_config",
    "import_config",
    "scrub_config",
]

# Only portable, non-secret preferences move between machines.
EXPORTABLE_KEYS: Set[str] = {
    "proxy",
    "cookie_browser",
    "cookies_file",
    "smart_mode",
    "lang",
    "theme",
    "limit_rate",
    "telegram_notify",
    "watch_clipboard",
}

SECRET_KEY_HINTS: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "auth",
    "session",
    "private",
)


def _looks_secret(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in SECRET_KEY_HINTS)


def scrub_config(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Keep only exportable, non-secret config keys.

    Parameters
    ----------
    data : Mapping[str, Any]
        Full config mapping.

    Returns
    -------
    dict
        Safe subset for export.

    Examples
    --------
    >>> sorted(scrub_config({"proxy": "http://x:1", "telegram_bot_token": "t"}))
    ['proxy']
    """
    cleaned: Dict[str, Any] = {}
    for key, value in data.items():
        if _looks_secret(key):
            continue
        if key in EXPORTABLE_KEYS:
            cleaned[key] = value
    return cleaned


def export_config(path: str | Path, data: Mapping[str, Any] | None = None) -> Path:
    """Write a portable config snapshot to *path*.

    Parameters
    ----------
    path : str or pathlib.Path
        Output JSON path.
    data : Mapping, optional
        Source config; defaults to :func:`smart_dl.core.config.load_config`.

    Returns
    -------
    pathlib.Path
        Path written.

    Raises
    ------
    OSError
        When the file cannot be written.
    """
    from smart_dl.core.config import load_config

    payload = scrub_config(data if data is not None else load_config())
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        {
            "app": "smart-dl",
            "schema": "config-export/1",
            "config": payload,
        },
        indent=2,
        ensure_ascii=False,
    )
    out.write_text(text + "\n", encoding="utf-8")
    return out


def import_config(path: str | Path, *, merge: bool = True) -> Dict[str, Any]:
    """Load a portable config snapshot into the live config.

    Unknown keys and secret-looking keys are dropped.

    Parameters
    ----------
    path : str or pathlib.Path
        JSON file created by :func:`export_config` or a bare config object.
    merge : bool, optional
        When ``True``, update live config in place; when ``False`` only
        return the parsed safe subset without saving.

    Returns
    -------
    dict
        The safe keys that were applied/parsed.

    Raises
    ------
    ValueError
        If the file is missing or not valid JSON object.
    """
    from smart_dl.core.config import load_config, save_config

    src = Path(path)
    if not src.is_file():
        raise ValueError(f"config export not found: {src}")
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("config export must be a JSON object")

    if "config" in raw and isinstance(raw["config"], dict):
        inner = raw["config"]
    else:
        inner = raw
    safe = scrub_config(inner)
    if merge:
        cfg = load_config()
        cfg.update(safe)
        save_config(cfg)
    return safe
