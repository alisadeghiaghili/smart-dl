"""SmartDL — Resilient media downloader for unstable networks."""
import subprocess
import sys
import time
from importlib.util import find_spec

VERSION = "3.0.0"

def ensure_deps():
    """Auto-install missing Python packages on first run."""
    deps = {"yt_dlp": "yt-dlp", "requests": "requests", "rich": "rich"}
    missing = [(mod, pkg) for mod, pkg in deps.items() if find_spec(mod) is None]
    if not missing:
        return
    total = len(missing)
    W = 30
    def _bar(done):
        f = int(W * done / total) if total else 0
        return "[" + "\u2588" * f + "\u2591" * (W - f) + "]"
    names = ", ".join(p for _, p in missing)
    print("\n  SmartDL needs " + str(total) + " missing package(s): " + names + "\n")
    SPIN = ["\u280b","\u2819","\u2839","\u2838","\u283c","\u2834","\u2826","\u2827","\u2807","\u280f"]
    for i, (mod, pkg) in enumerate(missing, 1):
        proc = subprocess.Popen(
            [sys.executable, "-m", "pip", "install", "--quiet", pkg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        s = 0
        while proc.poll() is None:
            sys.stdout.write("\r  " + _bar(i-1) + "  " + str(i) + "/" + str(total) + "  " + SPIN[s % len(SPIN)] + " Installing: " + pkg)
            sys.stdout.flush(); s += 1; time.sleep(0.1)
        if proc.returncode != 0:
            print("\n  [ERROR] Failed to install " + pkg + ". Try: pip install " + pkg)
            sys.exit(1)
        sys.stdout.write("\r  " + _bar(i) + "  " + str(i) + "/" + str(total) + "  \u2713 Installed: " + pkg + " " * 15 + "\n")
        sys.stdout.flush()
    print("  All " + str(total) + " package(s) installed successfully.\n")

ensure_deps()
