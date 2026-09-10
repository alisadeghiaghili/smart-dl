"""Windows console entry used by PyInstaller.

Kept separate from package code so the frozen executable starts the
interactive app without relying on ``python -m``.
"""

from __future__ import annotations

import sys


def run() -> int:
    """Start the interactive SmartDL app.

    Returns
    -------
    int
        Process exit code.
    """
    from smart_dl import deps_available, ensure_deps

    if not deps_available():
        # Frozen builds already bundle deps; this path is for source runs.
        if not ensure_deps():
            return 1
    from smart_dl.main import main as interactive_main

    interactive_main()
    return 0


if __name__ == "__main__":
    sys.exit(run())
