"""CLI smart-mode flag handlers."""

from __future__ import annotations

from typing import Any, Optional

__all__ = ["handle_smart_mode_flag"]


def handle_smart_mode_flag(
    mode: Optional[str],
    *,
    default_quality: Optional[str] = None,
    default_format: Optional[str] = None,
) -> bool:
    """Apply ``--smart-mode`` / default quality-format flags.

    Parameters
    ----------
    mode : str or None
        ``on``, ``off``, ``config``, or ``None`` to skip.
    default_quality : str, optional
        Persist default quality when provided.
    default_format : str, optional
        Persist default container format when provided.

    Returns
    -------
    bool
        ``True`` when the CLI should continue (URLs may follow);
        ``False`` when the command is terminal.
    """
    if not mode:
        return True

    from smart_dl.core.downloader import (
        get_smart_mode,
        interactive_smart_mode,
        save_smart_mode,
    )

    if mode == "config":
        interactive_smart_mode()
        return False

    prefs: dict[str, Any] = get_smart_mode()
    prefs["enabled"] = mode == "on"
    save_smart_mode(prefs)

    from smart_dl.ui import success, warn

    state = "enabled 🧠" if prefs["enabled"] else "disabled 😴"
    if prefs["enabled"]:
        success(f"Smart Mode {state}.")
    else:
        warn(f"Smart Mode {state}.")

    if default_quality:
        prefs["quality"] = default_quality
        save_smart_mode(prefs)
    if default_format:
        prefs["format"] = default_format
        save_smart_mode(prefs)
    return True
