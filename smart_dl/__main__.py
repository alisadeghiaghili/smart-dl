"""Entry point for ``python -m smart_dl``."""

from __future__ import annotations

import sys

from smart_dl import deps_available, ensure_deps


def main() -> int:
    """Bootstrap dependencies and run the interactive UI.

    Returns
    -------
    int
        Process exit code.
    """
    if not deps_available():
        if not ensure_deps():
            return 1
    from smart_dl.main import main as interactive_main

    interactive_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
