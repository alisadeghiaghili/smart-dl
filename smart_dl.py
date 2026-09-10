"""Interactive bootstrap — ``python smart_dl.py``."""

from __future__ import annotations

import sys

from smart_dl import VERSION, deps_available, ensure_deps


def _bootstrap() -> int:
    """Ensure dependencies then run the interactive app.

    Returns
    -------
    int
        Process exit code.
    """
    if not deps_available():
        if not ensure_deps():
            return 1
    from smart_dl.main import main

    main()
    return 0


if __name__ == "__main__":
    sys.exit(_bootstrap())

__all__ = ["VERSION", "_bootstrap"]
