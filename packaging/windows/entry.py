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
    # Frozen builds (PyInstaller) bundle all deps — skip pip check.
    if not getattr(sys, "frozen", False):
        from smart_dl import deps_available, ensure_deps

        if not deps_available():
            if not ensure_deps():
                return 1

    from smart_dl.main import main as interactive_main

    interactive_main()
    return 0


if __name__ == "__main__":
    try:
        code = run()
    except KeyboardInterrupt:
        code = 0
    except Exception as exc:
        # Keep the console window open so the user can read the error.
        print(f"\nError: {exc}")
        print("\nPress Enter to close...")
        try:
            input()
        except EOFError:
            pass
        code = 1
    sys.exit(code)
