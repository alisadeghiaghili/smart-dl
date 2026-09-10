"""Portable mode — run from a USB stick without touching system directories."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from smart_dl.core.paths import (
    disable_portable_mode as _disable_portable_mode,
)
from smart_dl.core.paths import (
    enable_portable_mode as _enable_portable_mode,
)
from smart_dl.core.paths import (
    get_app_root,
    get_config_path,
    get_data_dir,
    is_portable,
)

__all__ = [
    "disable_portable_mode",
    "enable_portable_mode",
    "get_app_root",
    "get_config_path",
    "get_data_dir",
    "get_db_dir",
    "is_portable",
]


def get_db_dir() -> Path:
    """Return the directory that holds SQLite databases.

    Returns
    -------
    pathlib.Path
        Same as :func:`smart_dl.core.paths.get_data_dir`.
    """
    return get_data_dir()


def enable_portable_mode(marker: Optional[str] = None) -> Path:
    """Enable portable mode by creating a marker file.

    Parameters
    ----------
    marker : str, optional
        Marker filename (default ``portable.txt``).

    Returns
    -------
    pathlib.Path
        Path of the created marker.
    """
    return _enable_portable_mode(marker)


def disable_portable_mode() -> None:
    """Disable portable mode by removing marker files."""
    _disable_portable_mode()
