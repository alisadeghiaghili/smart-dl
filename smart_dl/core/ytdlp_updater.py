"""Opt-in yt-dlp auto-update (roadmap R2)."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Callable, Optional, Tuple

__all__ = [
    "auto_update_allowed",
    "get_yt_dlp_version",
    "should_update_ytdlp",
    "update_yt_dlp",
]

Installer = Callable[[str], int]


def auto_update_allowed() -> bool:
    """Return True when silent yt-dlp update is explicitly enabled.

    Returns
    -------
    bool
        ``True`` if ``SMARTDL_UPDATE_YTDLP`` is ``1``/``true``/``yes``.
    """
    raw = os.environ.get("SMARTDL_UPDATE_YTDLP", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def should_update_ytdlp(flag: Optional[bool] = None) -> bool:
    """Whether an update should run this invocation.

    Parameters
    ----------
    flag : bool, optional
        CLI ``--update-ytdlp`` value. ``None`` means flag not passed.

    Returns
    -------
    bool
    """
    if flag is True:
        return True
    return auto_update_allowed()


def get_yt_dlp_version() -> str:
    """Return the installed yt-dlp version string.

    Returns
    -------
    str
        Version text, or ``"unknown"`` when yt-dlp is missing.
    """
    try:
        from yt_dlp.version import __version__ as ytdlp_version

        return str(ytdlp_version)
    except Exception:
        pass
    try:
        import yt_dlp

        ver = getattr(yt_dlp, "version", None)
        if ver is not None and hasattr(ver, "__version__"):
            return str(ver.__version__)
        if ver is not None and isinstance(ver, str):
            return ver
        return str(getattr(yt_dlp, "__version__", "unknown"))
    except Exception:
        return "unknown"


def _default_installer(pip_name: str) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", pip_name],
        check=False,
    )
    return int(proc.returncode)


def update_yt_dlp(installer: Optional[Installer] = None) -> Tuple[bool, str]:
    """Upgrade the yt-dlp package (opt-in path).

    Parameters
    ----------
    installer : Callable[[str], int], optional
        Custom installer; defaults to ``python -m pip install --upgrade yt-dlp``.

    Returns
    -------
    (bool, str)
        Success flag and a human message (versions or error).

    Examples
    --------
    >>> update_yt_dlp(installer=lambda pkg: 0)  # doctest: +SKIP
    (True, '...')
    """
    from smart_dl.ui import info, success, warn

    before = get_yt_dlp_version()
    info(f"Updating yt-dlp (installed: {before})...")
    install = installer or _default_installer
    try:
        code = install("yt-dlp")
    except Exception as exc:  # noqa: BLE001
        warn(f"yt-dlp update failed: {exc}")
        return False, str(exc)
    if code != 0:
        warn(f"yt-dlp update failed (exit {code})")
        return False, f"exit {code}"
    after = get_yt_dlp_version()
    if before == after:
        info(f"yt-dlp already current ({after})")
    else:
        success(f"yt-dlp updated: {before} → {after}")
    return True, f"{before} → {after}"
