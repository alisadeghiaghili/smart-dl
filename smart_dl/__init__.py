"""SmartDL — Resilient media downloader for unstable networks."""

from __future__ import annotations

import os
import subprocess
import sys
from importlib.util import find_spec
from typing import Callable, Dict, List, Optional

VERSION = "3.12.1"

__all__ = ["VERSION", "ensure_deps", "deps_available", "missing_deps"]

_RUNTIME_DEPS: Dict[str, str] = {
    "yt_dlp": "yt-dlp",
    "requests": "requests",
    "rich": "rich",
}


def _auto_install_allowed() -> bool:
    """Return True when silent auto-install is explicitly enabled."""
    return bool(os.environ.get("SMARTDL_AUTO_DEPS"))


def deps_available() -> bool:
    """Check whether all runtime dependencies import cleanly.

    Returns
    -------
    bool
        ``True`` if yt-dlp, requests, and rich are importable.
    """
    return all(find_spec(mod) is not None for mod in _RUNTIME_DEPS)


def missing_deps() -> List[str]:
    """List distribution names of missing runtime dependencies.

    Returns
    -------
    list of str
        Pip package names, empty when everything is present.
    """
    return [pkg for mod, pkg in _RUNTIME_DEPS.items() if find_spec(mod) is None]


def ensure_deps(
    *,
    allow_auto_install: Optional[bool] = None,
    installer: Optional[Callable[[str], int]] = None,
) -> bool:
    """Ensure runtime dependencies are installed.

    By default this **does not** run pip. It only auto-installs when
    ``SMARTDL_AUTO_DEPS=1`` is set or *allow_auto_install* is ``True``.

    Parameters
    ----------
    allow_auto_install : bool, optional
        Override the environment flag. ``True`` enables pip install.
    installer : Callable[[str], int], optional
        Custom installer taking a package name and returning an exit code.
        Defaults to ``python -m pip install``.

    Returns
    -------
    bool
        ``True`` if all dependencies are present after the call.

    Examples
    --------
    >>> ensure_deps(allow_auto_install=False)  # doctest: +SKIP
    True
    """
    missing = missing_deps()
    if not missing:
        return True

    if allow_auto_install is None:
        allow_auto_install = _auto_install_allowed()
    if not allow_auto_install:
        print(
            "\n  Missing packages: "
            + ", ".join(missing)
            + "\n  Install with: pip install "
            + " ".join(missing)
            + "\n  Or set SMARTDL_AUTO_DEPS=1 to install automatically.\n"
        )
        return False

    def _default_installer(pkg: str) -> int:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", pkg],
            check=False,
        )
        return int(proc.returncode)

    install = installer or _default_installer
    total = len(missing)
    width = 30

    def _bar(done: int) -> str:
        filled = int(width * done / total) if total else 0
        return "[" + "█" * filled + "░" * (width - filled) + "]"

    print("\n  SmartDL needs " + str(total) + " missing package(s): " + ", ".join(missing) + "\n")
    for index, pkg in enumerate(missing, 1):
        sys.stdout.write(
            "\r  "
            + _bar(index - 1)
            + "  "
            + str(index)
            + "/"
            + str(total)
            + "  Installing: "
            + pkg
        )
        sys.stdout.flush()
        code = install(pkg)
        if code != 0:
            print("\n  [ERROR] Failed to install " + pkg + ". Try: pip install " + pkg)
            return False
        sys.stdout.write(
            "\r  "
            + _bar(index)
            + "  "
            + str(index)
            + "/"
            + str(total)
            + "  ✓ Installed: "
            + pkg
            + " " * 15
            + "\n"
        )
        sys.stdout.flush()
    print("  All " + str(total) + " package(s) installed successfully.\n")
    return deps_available()
