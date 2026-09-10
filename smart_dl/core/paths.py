"""Filesystem locations for config, databases, and default downloads.

All persistent state lives under a single data directory so portable mode
and normal installs behave consistently.

Examples
--------
>>> from smart_dl.core.paths import get_data_dir, get_config_path
>>> data = get_data_dir()  # doctest: +SKIP
>>> cfg = get_config_path()  # doctest: +SKIP
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

__all__ = [
    "disable_portable_mode",
    "enable_portable_mode",
    "get_app_root",
    "get_config_path",
    "get_data_dir",
    "get_db_path",
    "get_default_download_dir",
    "is_portable",
]

_PORTABLE_MARKERS = ("portable.txt", ".portable")


def get_app_root() -> Path:
    """Return the project/install root used for portable-mode markers.

    Returns
    -------
    pathlib.Path
        Parent of the ``smart_dl`` package (repo root when running from source).
    """
    return Path(__file__).resolve().parent.parent.parent


def is_portable() -> bool:
    """Check whether portable mode is active via a marker file next to the app.

    Returns
    -------
    bool
        ``True`` if ``portable.txt`` or ``.portable`` exists under the app root.
    """
    root = get_app_root()
    return any((root / name).exists() for name in _PORTABLE_MARKERS)


def get_data_dir() -> Path:
    """Return (and create) the application data directory.

    Portable mode uses ``<app_root>/data``. Otherwise:

    * Windows: ``%APPDATA%/SmartDL``
    * POSIX: ``~/.smartdl``

    Returns
    -------
    pathlib.Path
        Absolute path to an existing directory.
    """
    if is_portable():
        data_dir = get_app_root() / "data"
    elif os.name == "nt":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        data_dir = base / "SmartDL"
    else:
        data_dir = Path.home() / ".smartdl"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_path() -> Path:
    """Return the path of ``config.json`` inside the data directory.

    Returns
    -------
    pathlib.Path
        Path to the config file (may not exist yet).
    """
    return get_data_dir() / "config.json"


def get_db_path(name: str) -> Path:
    """Return a SQLite database path under the data directory.

    Parameters
    ----------
    name : str
        Database name with or without ``.db`` suffix (e.g. ``"history"``).

    Returns
    -------
    pathlib.Path
        Absolute path to the database file.
    """
    filename = name if name.endswith(".db") else f"{name}.db"
    return get_data_dir() / filename


def get_default_download_dir() -> Path:
    """Return the default media output directory.

    Returns
    -------
    pathlib.Path
        ``~/Downloads/SmartDL`` (not necessarily created yet).
    """
    return Path.home() / "Downloads" / "SmartDL"


def enable_portable_mode(marker: Optional[str] = None) -> Path:
    """Create a portable-mode marker file.

    Parameters
    ----------
    marker : str, optional
        Marker filename. Defaults to ``portable.txt``.

    Returns
    -------
    pathlib.Path
        Path of the marker file that was created.
    """
    path = get_app_root() / (marker or _PORTABLE_MARKERS[0])
    path.touch()
    return path


def disable_portable_mode() -> None:
    """Remove portable-mode marker files if present."""
    root = get_app_root()
    for name in _PORTABLE_MARKERS:
        marker = root / name
        if marker.exists():
            marker.unlink()
