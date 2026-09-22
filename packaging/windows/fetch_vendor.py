"""Fetch the external tools that the onefile build embeds, into ``vendor/``.

The onefile release asset is meant to be fully self-contained — no ffmpeg,
node, or aria2c required on the target machine. This script downloads those
tools once at build time so PyInstaller can bundle them under ``vendor/``.

Layout produced (each tool in its own folder, so the runtime PATH shim can
just prepend each folder):

    vendor/
      ffmpeg/ffmpeg.exe  vendor/ffmpeg/ffprobe.exe
      node/node.exe
      aria2/aria2c.exe   (+ any DLLs aria2 ships next to it)

Sources:
  * ffmpeg — BtbN's static win64 build (self-contained exes, no extra DLLs).
    Same upstream the app itself recommends.
  * node   — pinned Node.js LTS official zip (reproducible build).
  * aria2  — pinned official Windows build from the aria2 GitHub releases
    (self-contained exe + its lib/ DLLs; no winget/runner dependency).

Run from anywhere:

    python packaging/windows/fetch_vendor.py [--clean]

It is idempotent: a tool already present and valid is left alone. It exits
non-zero if any tool is missing after the run, so a CI step that requires a
fully-embedded build will fail rather than ship an incomplete exe.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# Pinned Node.js LTS for a reproducible build. Bump deliberately.
NODE_VERSION = "v20.18.0"
NODE_URL = f"https://nodejs.org/dist/{NODE_VERSION}/node-{NODE_VERSION}-win-x64.zip"

# BtbN static (non-shared) win64 build — a stable, permanent redirect.
FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/"
    "latest/download/ffmpeg-master-latest-win64-gpl.zip"
)

# Pinned aria2 Windows build from the official GitHub releases (reproducible,
# no winget/runner dependency). Layout: <ver>/bin/aria2c.exe + <ver>/lib/*.dll.
ARIA2_VERSION = "1.37.0"
ARIA2_URL = (
    f"https://github.com/aria2/aria2/releases/download/"
    f"aria2-{ARIA2_VERSION}/aria2-{ARIA2_VERSION}-win-64bit-build1.zip"
)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
EXPECTED = {"ffmpeg", "node", "aria2"}


def _log(msg: str) -> None:
    print(f"[fetch_vendor] {msg}", flush=True)


def _download(url: str, dest: Path) -> None:
    """Download *url* to *dest*, following redirects."""
    _log(f"download {url}")
    with urllib.request.urlopen(url, timeout=300) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)
    if dest.stat().st_size == 0:
        raise RuntimeError(f"empty download: {url}")


def _validate(name: str, exe: Path, flag: str = "-version") -> None:
    """Best-effort: run the binary and confirm it is not empty/corrupt."""
    if not exe.is_file() or exe.stat().st_size == 0:
        raise RuntimeError(f"{name}: missing or empty at {exe}")
    try:
        subprocess.run([str(exe), flag], capture_output=True, timeout=30)
    except Exception as exc:  # noqa: BLE001 — validation is best-effort
        _log(f"warn: could not run {name} for sanity check: {exc!r}")


def fetch_ffmpeg(dest: Path) -> None:
    exe = dest / "ffmpeg.exe"
    if exe.is_file():
        _log("ffmpeg: already present")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zpath = tmp_path / "ffmpeg.zip"
        _download(FFMPEG_URL, zpath)
        with zipfile.ZipFile(zpath) as z:
            names = [n for n in z.namelist() if n.endswith(("ffmpeg.exe", "ffprobe.exe"))]
            if not any(n.endswith("ffmpeg.exe") for n in names):
                raise RuntimeError("ffmpeg.exe not found in BtbN archive")
            for n in names:
                z.extract(n, tmp_path)
        for tool in ("ffmpeg.exe", "ffprobe.exe"):
            src = next((tmp_path / n) for n in names if n.endswith(tool))
            shutil.copy2(src, dest / tool)
    _validate("ffmpeg", dest / "ffmpeg.exe")


def fetch_node(dest: Path) -> None:
    exe = dest / "node.exe"
    if exe.is_file():
        _log("node: already present")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zpath = tmp_path / "node.zip"
        _download(NODE_URL, zpath)
        with zipfile.ZipFile(zpath) as z:
            node_name = next(n for n in z.namelist() if n.endswith("/node.exe"))
            z.extract(node_name, tmp_path)
        shutil.copy2(tmp_path / node_name, dest / "node.exe")
    _validate("node", dest / "node.exe", flag="--version")


def fetch_aria2(dest: Path) -> None:
    exe = dest / "aria2c.exe"
    if exe.is_file():
        _log("aria2: already present")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        zpath = tmp_path / "aria2.zip"
        _download(ARIA2_URL, zpath)
        with zipfile.ZipFile(zpath) as z:
            bin_names = [n for n in z.namelist() if n.endswith("aria2c.exe")]
            if not bin_names:
                raise RuntimeError("aria2c.exe not found in aria2 archive")
            bin_dir = Path(bin_names[0]).parent
            for n in bin_names:
                z.extract(n, tmp_path)
            # aria2c.exe needs its DLLs (libssl/libcrypto/libcrypto, etc.)
            # from <ver>/lib/ shipped alongside it.
            for n in z.namelist():
                if n.startswith(bin_dir.as_posix() + "/lib/"):
                    z.extract(n, tmp_path)
        shutil.copy2(tmp_path / bin_names[0], exe)
        lib_dir = tmp_path / bin_dir / "lib"
        if lib_dir.is_dir():
            for dll in lib_dir.glob("*.dll"):
                shutil.copy2(dll, dest / dll.name)
    _validate("aria2", exe, flag="--version")


FETCHERS = {"ffmpeg": fetch_ffmpeg, "node": fetch_node, "aria2": fetch_aria2}


def main(argv: list[str]) -> int:
    clean = "--clean" in argv
    if clean and VENDOR_DIR.is_dir():
        shutil.rmtree(VENDOR_DIR)
        _log("removed existing vendor/")
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for name, fetcher in FETCHERS.items():
        tool_dir = VENDOR_DIR / name
        tool_dir.mkdir(parents=True, exist_ok=True)
        try:
            fetcher(tool_dir)
            _log(f"{name}: OK")
        except Exception as exc:  # noqa: BLE001 — report, then continue to next tool
            failures.append(f"{name}: {exc}")
            _log(f"{name}: FAILED — {exc}")

    if failures:
        _log("MISSING TOOLS (fully-embedded build unavailable): " + "; ".join(failures))
        return 1

    _log(f"all vendor tools present under {VENDOR_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
