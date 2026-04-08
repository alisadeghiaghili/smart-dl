#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ┌─────────────────────────────────────────────────────────────┐
# │  ░██████╗███╗░░░███╗░█████╗░██████╗░████████╗██████╗░██╗░░ │
# │  ██╔════╝████╗░████║██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██║░░ │
# │  ╚█████╗░██╔████╔██║███████║██████╔╝░░░██║░░░██║░░██║██║░░ │
# │  ░╚═══██╗██║╚██╔╝██║██╔══██║██╔══██╗░░░██║░░░██║░░██║██║░░ │
# │  ██████╔╝██║░╚═╝░██║██║░░██║██║░░██║░░░██║░░░██████╔╝█████╗│
# │  ╚═════╝░╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░╚════╝│
# ├─────────────────────────────────────────────────────────────┤
# │  author  ──  Hellch!ef  ·  if u know u know                 │
# │  built   ──  2026-04-09  ·  Tehran, IR                      │
# │  stack   ──  yt-dlp · rich · requests                       │
# │  motto   ──  "bad connection? hold my retry loop."          │
# └─────────────────────────────────────────────────────────────┘

import os, sys, time, signal, threading, traceback, re, subprocess
from pathlib import Path
from urllib.parse import urlparse

# ─── Bootstrap (pre-rich) ─────────────────────────────────────────────────────
def ensure_deps():
    import importlib
    deps = {"yt_dlp": "yt-dlp", "requests": "requests", "rich": "rich"}
    missing = [(mod, pkg) for mod, pkg in deps.items() if not importlib.util.find_spec(mod)]
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

import yt_dlp, requests
from rich.console import Console
from rich.progress import (Progress, SpinnerColumn, BarColumn, TextColumn,
                           DownloadColumn, TransferSpeedColumn, TimeRemainingColumn, TaskProgressColumn)
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich.padding import Padding
from rich import box

console = Console(highlight=False)

LOGO = r"""
 ____                       _   ____  _
/ ___| _ __ ___   __ _ _ __| |_|  _ \| |
\___ \| '_' ` _ \ / _` | '__| __| | | | |
 ___) | | | | | | (_| | |  | |_| |_| | |___
|____/|_| |_| |_|\__,_|_|   \__|____/|_____|
"""
VERSION = "2.2.0"
