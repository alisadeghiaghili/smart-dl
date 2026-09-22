"""Windows console entry used by PyInstaller.

Kept separate from package code so the frozen executable starts the
interactive app without relying on ``python -m``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _install_vendor_path() -> None:
    """Prepend bundled external tools to PATH so a frozen exe is self-contained.

    The onefile build bundles ``vendor/{ffmpeg,node,aria2}`` (see
    fetch_vendor.py / build_inputs.py) next to the app. The app and yt-dlp
    locate these tools by bare name (``ffmpeg``, ``node``, ``aria2c``) via
    :func:`shutil.which`, which reads ``PATH``. Prepending each vendor folder
    to PATH makes them resolvable without touching the download engine.

    Does nothing when not frozen or when the vendor dir is absent (the onedir
    build and source runs fall back to the system PATH, as before).
    """
    if not getattr(sys, "frozen", False):
        return
    meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    vendor = meipass / "vendor"
    if not vendor.is_dir():
        return
    path = os.environ.get("PATH", "")
    parts = path.split(os.pathsep)
    for folder in sorted(vendor.iterdir()):
        if folder.is_dir() and folder.name not in parts:
            parts.insert(0, str(folder))
    os.environ["PATH"] = os.pathsep.join(parts)


def _force_utf8_stdio() -> None:
    """Make a frozen exe print the banner regardless of the console codepage.

    PyInstaller wires the console to the system ANSI codepage (often cp1252)
    rather than UTF-8. The UI prints characters like ``☕`` and ``·`` that
    cp1252 cannot encode, so the app would crash on startup under such a
    console. Reconfiguring stdout/stderr to UTF-8 (with replacement for any
    still-unencodable glyph) keeps the frozen UI alive. Source runs use the
    interpreter's own stdio and are left untouched.
    """
    if not getattr(sys, "frozen", False):
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def run() -> int:
    """Start the interactive SmartDL app.

    Returns
    -------
    int
        Process exit code.
    """
    # Force a UTF-8 console so the banner renders under any codepage.
    _force_utf8_stdio()

    # Make bundled external tools (ffmpeg/node/aria2c) resolvable on PATH.
    # Must run before any module that shells out is used.
    _install_vendor_path()

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
