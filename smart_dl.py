#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ┌─────────────────────────────────────────────────────────────┐
# │  ░██████╗███╗░░░███╗░█████╗░██████╗░████████╗██████╗░██╗░░  │
# │  ██╔════╝████╗░████║██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██║░░  │
# │  ╚█████╗░██╔████╔██║███████║██████╔╝░░░██║░░░██║░░██║██║░░  │
# │  ░╚═══██╗██║╚██╔╝██║██╔══██║██╔══██╗░░░██║░░░██║░░██║██║░░  │
# │  ██████╔╝██║░╚═╝░██║██║░░██║██║░░██║░░░██║░░░██████╔╝█████╗ │
# │  ╚═════╝░╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░╚════╝ │
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
    from importlib.util import find_spec
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
\___ \| '_ ` _ \ / _` | '__| __| | | | |
 ___) | | | | | | (_| | |  | |_| |_| | |___
|____/|_| |_| |_|\__,_|_|   \__|____/|_____|
"""
VERSION = "2.3.1"

# ─── Download settings (user-configurable) ───────────────────────────────────
DL_SETTINGS = {
    "max_retries":   999,   # 0 = infinite
    "fragments":     4,     # concurrent fragment downloads (1-16)
}

def _settings_menu():
    while True:
        console.print()
        r = DL_SETTINGS["max_retries"]
        f = DL_SETTINGS["fragments"]
        retry_label = "infinite" if r >= 999 else str(r)
        t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
        t.add_column(style="bold cyan", width=4, justify="right")
        t.add_column(style="white")
        t.add_row("1", "Max retries      [dim](current: [bold]" + retry_label + "[/bold]  ·  default: infinite)[/dim]")
        t.add_row("2", "Fragment threads [dim](current: [bold]" + str(f) + "[/bold]  ·  default: 4  ·  range: 1-16)[/dim]")
        t.add_row("0", "Back")
        console.print(Panel(t, title="[bold cyan]  Download Settings[/bold cyan]",
                            border_style="cyan", padding=(0,1)))
        console.print(Padding(
            "[dim]  Tip: default values work best for most connections — "
            "change only if you know what you\'re doing.[/dim]", (0,2)))
        ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="0").strip()

        if ch == "0":
            break

        elif ch == "1":
            console.print(Padding(
                "[dim]  Enter 0 or 999 for infinite retries.[/dim]", (0,2)))
            val = Prompt.ask(
                "  [bold yellow]Max retries[/bold yellow] [dim](default: 999 = infinite)[/dim]",
                default="999"
            ).strip()
            if val.isdigit():
                DL_SETTINGS["max_retries"] = int(val) if int(val) < 999 else 999
                lbl = "infinite" if DL_SETTINGS["max_retries"] >= 999 else str(DL_SETTINGS["max_retries"])
                success("Max retries set to: " + lbl)
            else:
                warn("Invalid value — keeping current setting.")

        elif ch == "2":
            console.print()
            console.print(Panel(
                "[bold yellow]  Recommendation:[/bold yellow] keep between [bold]2[/bold] and [bold]8[/bold].\n\n"
                "  [dim]\u00b7 Too low  (1-2) \u2192 slower downloads, especially on unstable connections.\n"
                "  \u00b7 Optimal  (3-6) \u2192 best balance for most networks including weak/mobile.\n"
                "  \u00b7 High     (8+)  \u2192 may cause rate-limiting or errors on some servers.\n"
                "  \u00b7 Max     (16)   \u2192 not recommended; often counterproductive.[/dim]",
                border_style="yellow", title="[bold yellow]  Fragment Threads[/bold yellow]", padding=(0,2)
            ))
            val = Prompt.ask(
                "  [bold yellow]Fragment threads[/bold yellow] [dim](1-16, default: 4)[/dim]",
                default="4"
            ).strip()
            if val.isdigit() and 1 <= int(val) <= 16:
                DL_SETTINGS["fragments"] = int(val)
                if int(val) > 8:
                    warn("Value " + val + " is high \u2014 this may cause rate-limiting on some servers.")
                success("Fragment threads set to: " + val)
            else:
                warn("Invalid value \u2014 must be between 1 and 16.")
        else:
            warn("Invalid selection.")

# ─── Stop control ─────────────────────────────────────────────────────────────
stop_event = threading.Event()

def signal_handler(sig, frame):
    console.print("\n[bold yellow]  Stop requested...[/bold yellow]")
    stop_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ─── Helpers ──────────────────────────────────────────────────────────────────
def is_youtube_url(url):
    return any(h in urlparse(url).netloc for h in ["youtube.com","youtu.be","www.youtube.com"])

def fmt_size(b):
    if not b: return "?"
    for unit in ["B","KB","MB","GB"]:
        if b < 1024: return str(round(b,1)) + " " + unit
        b /= 1024
    return str(round(b,1)) + " TB"

def fmt_dur(s):
    if not s: return "?"
    return str(int(s//3600)).zfill(2) + ":" + str(int((s%3600)//60)).zfill(2) + ":" + str(int(s%60)).zfill(2)

def safe_filename(s, maxlen=80):
    return ("".join(c for c in s if c.isalnum() or c in " ._-()[]").strip() or "file")[:maxlen]
    
def print_header():
    console.print()
    console.print(Align(Text(LOGO.strip(), style="bold cyan"), align="center"))
    console.print(Align(Text("v" + VERSION + "  ·  Smart YouTube & Podcast Downloader  ·  Ctrl+C to stop", style="dim"), align="center"))
    console.print(Align(Text("by Hellch!ef  ·  if u know u know", style="dim italic"), align="center"))
    console.print(Align(Text("☕  buymeacoffee.com/alisadeghil", style="bold yellow"), align="center"))
    console.print(Rule(style="cyan"))
    console.print()

def _bye():
    console.print()
    console.print(Rule(style="cyan"))
    console.print(Align(Text("bye ❤", style="bold cyan"), align="center"))
    console.print(Align(Text("☕  buymeacoffee.com/alisadeghil", style="bold yellow"), align="center"))
    console.print(Rule(style="cyan"))
    console.print()

def print_section(title, icon=""):
    console.print()
    console.print(Rule("[bold cyan]" + icon + "  " + title + "[/bold cyan]", style="cyan"))

def success(msg): console.print("[bold green]  \u2713  " + msg + "[/bold green]")
def warn(msg):    console.print("[yellow]  \u26a0  " + msg + "[/yellow]")
def error(msg):   console.print("[bold red]  \u2717  " + msg + "[/bold red]")
def info(msg):    console.print("[dim]  \u00b7  " + msg + "[/dim]")

# ─── Config persistence ────────────────────────────────────────────────────────
import json as _json_mod

_SMARTDL_CONFIG = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "SmartDL", "config.json"
)

def _load_config() -> dict:
    try:
        with open(_SMARTDL_CONFIG, "r", encoding="utf-8") as _f:
            return _json_mod.load(_f)
    except Exception:
        return {}

def _save_config(data: dict):
    try:
        os.makedirs(os.path.dirname(_SMARTDL_CONFIG), exist_ok=True)
        with open(_SMARTDL_CONFIG, "w", encoding="utf-8") as _f:
            _json_mod.dump(data, _f, indent=2)
    except Exception:
        pass

# ─── ffmpeg check ─────────────────────────────────────────────────────────────
def _has_ffmpeg():
    try:
        subprocess.run(["ffmpeg","-version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False

# ─── ffmpeg warning ───────────────────────────────────────────────────────────
def _warn_no_ffmpeg(action="convert to MP3"):
    msg = (
        "[bold yellow]  ffmpeg not found![/bold yellow]\n\n"
        "  ffmpeg is required to " + action + ".\n"
        "  Install it with:\n\n"
        "    [bold cyan]winget install Gyan.FFmpeg[/bold cyan]\n\n"
        "  Then close and reopen the terminal."
    )
    console.print()
    console.print(Panel(msg, border_style="yellow",
                        title="[bold yellow]  Missing dependency[/bold yellow]",
                        padding=(0, 2)))

# ─── Retry / backoff ──────────────────────────────────────────────────────────
_FATAL_ERRORS = [
    "ffmpeg is not installed", "ffmpeg not found", "abort-on-error",
    "aborting due to", "requested merging of multiple formats",
    "sign in to confirm", "video unavailable", "private video",
    "age-restricted", "copyright", "format not available",
]

def retry_with_backoff(func, max_retries=999, base_delay=5, max_delay=300):
    attempt, delay = 0, base_delay
    while not stop_event.is_set():
        try:
            return func()
        except Exception as e:
            msg = str(e).lower()
            if any(f in msg for f in _FATAL_ERRORS):
                raise
            attempt += 1
            is_net = any(x in msg for x in [
                "connection","timeout","network","reset","refused","broken pipe",
                "ssl","certificate","name or service","temporary failure",
                "unreachable","no route","http error 5","503","502","429","rate limit",
            ])
            if attempt >= max_retries and not is_net:
                raise
            if stop_event.is_set():
                break
            delay = min(delay * 1.5, max_delay)
            warn("Error (attempt " + str(attempt) + "): " + str(e)[:80])
            info("Retrying in " + str(int(delay)) + "s...")
            for _ in range(int(delay)):
                if stop_event.is_set(): return None
                time.sleep(1)
    return None

# ─── yt-dlp logger & progress hook ───────────────────────────────────────────
_SUPPRESS_WARNINGS = [
    "no supported javascript runtime", "js runtime", "--js-runtimes",
    "youtube extraction without a js", "writing dash", "only some players",
]

_ERROR_HINTS = [
    ("ffmpeg is not installed",              "Fix: winget install Gyan.FFmpeg  (then reopen terminal)"),
    ("requested merging of multiple formats","Fix: winget install Gyan.FFmpeg  (then reopen terminal)"),
    ("private video",                        "This video is private — cannot be downloaded."),
    ("sign in to confirm",                   "Age-restricted — YouTube requires sign-in."),
    ("age-restricted",                       "Age-restricted — cannot download without authentication."),
    ("video unavailable",                    "Video unavailable (deleted, region-blocked, or private)."),
    ("blocked in your country",              "Geo-blocked. Try a VPN."),
    ("not available in your country",        "Geo-blocked. Try a VPN."),
    ("copyright",                            "Blocked due to a copyright claim."),
    ("requested format is not available",    "Selected quality not available. Try a different format."),
    ("format not available",                 "Selected quality not available. Try a different format."),
    ("unable to extract",                    "Could not extract video info. URL may be invalid."),
    ("unsupported url",                      "Unsupported URL."),
    ("connection",                           "Network error — check connection or proxy (press P)."),
    ("timeout",                              "Connection timed out — check network or try again."),
    ("no such file",                         "Output path inaccessible. Check folder permissions."),
]

def _diagnose_error(e: Exception) -> str:
    msg = str(e).lower()
    for keyword, hint in _ERROR_HINTS:
        if keyword in msg:
            return hint
    return ""

class YTLogger:
    def debug(self, msg): pass
    def info(self, msg):  pass
    def warning(self, msg):
        if any(s in msg.lower() for s in _SUPPRESS_WARNINGS): return
        warn(msg)
    def error(self, msg):
        if not stop_event.is_set(): error(msg)

_progress_ctx: dict = {"obj": None, "task": None, "last": 0}

def yt_hook(d):
    if stop_event.is_set():
        raise yt_dlp.utils.DownloadError("Stopped by user")
    p = _progress_ctx
    if d["status"] == "downloading" and p["obj"] and p["task"] is not None:
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or None
        done  = d.get("downloaded_bytes", 0)
        fname = Path(d.get("filename","")).name
        p["obj"].update(p["task"], completed=done, total=total,
                        description="[cyan]" + fname[:50] + "[/cyan]")
        p["last"] = done
    elif d["status"] == "finished" and p["obj"] and p["task"] is not None:
        t = d.get("total_bytes", p["last"])
        p["obj"].update(p["task"], completed=t, total=t)

def make_progress():
    return Progress(
        SpinnerColumn(spinner_name="dots", style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=32, style="cyan", complete_style="bold green"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )

# ─── Proxy ────────────────────────────────────────────────────────────────────
def _get_current_proxy():
    # 1. env vars — check both uppercase (Windows/set by SmartDL) and lowercase (Linux/Mac system)
    env = (
        os.environ.get("HTTPS_PROXY") or
        os.environ.get("HTTP_PROXY") or
        os.environ.get("https_proxy") or
        os.environ.get("http_proxy") or
        ""
    )
    if env:
        return env

    # 2. saved config from previous session
    cfg_proxy = _load_config().get("proxy", "")
    if cfg_proxy:
        _apply_proxy(cfg_proxy)
        return cfg_proxy

    # 3. Windows system proxy (registry)
    try:
        import winreg as _wr
        key = _wr.OpenKey(_wr.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        enabled, _ = _wr.QueryValueEx(key, "ProxyEnable")
        if enabled:
            server, _ = _wr.QueryValueEx(key, "ProxyServer")
            if server:
                if "=" in server:
                    parts = dict(p.split("=",1) for p in server.split(";") if "=" in p)
                    server = parts.get("https") or parts.get("http") or server
                if not server.startswith("http"):
                    server = "http://" + server
                # Apply so env vars are set for this session and config is persisted
                _apply_proxy(server)
                return server
    except Exception:
        pass

    return ""

def _apply_proxy(addr):
    os.environ["HTTP_PROXY"]  = addr
    os.environ["HTTPS_PROXY"] = addr
    cfg = _load_config()
    cfg["proxy"] = addr
    _save_config(cfg)

def _clear_proxy():
    for k in ["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"]:
        os.environ.pop(k, None)
    cfg = _load_config()
    cfg["proxy"] = ""
    _save_config(cfg)

def _hint_proxy_port(addr):
    m = re.search(r':(\d+)$', addr)
    if not m: return
    port = int(m.group(1))
    hints = {10808: "SOCKS5", 1080: "SOCKS5", 9050: "SOCKS5", 9150: "SOCKS5"}
    if port in hints:
        warn("Port " + str(port) + " is typically used for " + hints[port] + ", not HTTP.")
        info("If the connection fails, try: socks5://" + addr.split("://",1)[-1])

def _proxy_menu():
    LOCALHOST_PORTS = [
        (10809, "v2rayN / Xray / Nekoray     (HTTP)"),
        (10808, "v2rayN / Xray / Nekoray     (SOCKS5)"),
        (7890,  "Clash / ClashX / MahsaNG   (HTTP)"),
        (7891,  "Clash / ClashX / MahsaNG   (SOCKS5)"),
        (2081,  "Hiddify                    (HTTP)"),
        (2080,  "Hiddify                    (SOCKS5)"),
        (1080,  "Generic SOCKS5"),
        (8080,  "Generic HTTP"),
    ]
    while True:
        console.print()
        t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
        t.add_column(style="bold cyan", width=4, justify="right")
        t.add_column(style="white")
        t.add_column(style="dim")
        t.add_row("1", "Enter proxy address manually", "(http://host:port or socks5://host:port)")
        t.add_row("2", "Use localhost port", "(v2rayN · Clash · Hiddify · Nekoray)")
        t.add_row("3", "I'm using a VPN", "(WireGuard · OpenVPN · AnyConnect)")
        t.add_row("4", "Clear proxy", "(none)")
        t.add_row("0", "Cancel / back", "")
        console.print(Panel(t, title="[bold cyan]  Proxy Setup[/bold cyan]",
                            border_style="cyan", padding=(0,1)))
        ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="0").strip()

        if ch == "0":
            break

        elif ch == "1":
            addr = Prompt.ask("  [bold yellow]Proxy address[/bold yellow]").strip()
            if addr:
                if not addr.startswith(("http://","https://","socks5://","socks4://")):
                    addr = "http://" + addr
                _apply_proxy(addr)
                _hint_proxy_port(addr)
                success("Proxy set: " + addr)
            break

        elif ch == "2":
            t2 = Table(box=box.ROUNDED, show_header=True, border_style="cyan", padding=(0,1))
            t2.add_column("#",       style="bold cyan", width=5,  justify="right")
            t2.add_column("Port",    style="white",     width=9)
            t2.add_column("Common use", style="dim",    width=32)
            t2.add_column("Address", style="cyan")
            for idx,(port,label) in enumerate(LOCALHOST_PORTS,1):
                t2.add_row(str(idx), str(port), label, "http://127.0.0.1:" + str(port))
            t2.add_row("C", "custom", "Enter a custom port", "")
            t2.add_row("0", "back", "Return to proxy menu", "")
            console.print(t2)
            sel = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="2").strip().lower()
            if sel == "0":
                continue
            if sel == "c":
                p = Prompt.ask("  [bold yellow]Port[/bold yellow]").strip()
                if p.isdigit():
                    addr = "http://127.0.0.1:" + p
                    _apply_proxy(addr); _hint_proxy_port(addr); success("Proxy set: " + addr)
            elif sel.isdigit() and 1 <= int(sel) <= len(LOCALHOST_PORTS):
                port, _ = LOCALHOST_PORTS[int(sel)-1]
                addr = "http://127.0.0.1:" + str(port)
                _apply_proxy(addr); _hint_proxy_port(addr); success("Proxy set: " + addr)
            break

        elif ch == "3":
            _clear_proxy()
            console.print(Panel(
                "[bold green]  Proxy cleared.[/bold green]\n\n"
                "  [dim]WireGuard, OpenVPN, and AnyConnect route traffic at the system\n"
                "  level — no local proxy needed. SmartDL will use your VPN directly.\n\n"
                "  If downloads were failing with a proxy set, this should fix it.[/dim]",
                border_style="green", title="[bold green]  VPN Mode[/bold green]", padding=(0, 2)
            ))
            break

        elif ch == "4":
            _clear_proxy(); success("Proxy cleared.")
            break
        else:
            warn("Invalid selection.")

# ─── Install menu ─────────────────────────────────────────────────────────────
def _install_menu():
    while True:
        has_ff = _has_ffmpeg()
        try:
            import shutil as _sh
            has_wt = bool(_sh.which("wt"))
        except Exception:
            has_wt = False

        console.print()
        t = Table(box=box.ROUNDED, show_header=False, border_style="magenta", padding=(0,2))
        t.add_column(style="bold magenta", width=4, justify="right")
        t.add_column(style="white")
        t.add_column(style="dim")
        t.add_row("1", "Install ffmpeg",
                  ("[green]\u2713 installed[/green]" if has_ff else "[red]\u2717 not found[/red]"))
        t.add_row("2", "Install Windows Terminal",
                  ("[green]\u2713 installed[/green]" if has_wt else "[red]\u2717 not found[/red]"))
        t.add_row("0", "Back", "")
        console.print(Panel(t, title="[bold magenta]  Install Dependencies[/bold magenta]",
                            border_style="magenta", padding=(0,1)))
        ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="0").strip()

        if ch == "0":
            break

        elif ch == "1":
            _install_ffmpeg()

        elif ch == "2":
            _install_wt()
            # offer relaunch inside WT
            try:
                import shutil as _sh2
                if _sh2.which("wt"):
                    ans = Prompt.ask(
                        "  [bold yellow]Relaunch SmartDL inside Windows Terminal now?[/bold yellow]",
                        default="y"
                    ).strip().lower()
                    if ans == "y":
                        _relaunch_in_wt()
            except Exception:
                pass
        else:
            warn("Invalid selection.")

def _install_ffmpeg():
    import shutil as _sh
    info("Trying winget...")
    try:
        r = subprocess.run(
            ["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements",
             "--accept-package-agreements"],
            timeout=180
        )
        if r.returncode == 0 and _sh.which("ffmpeg"):
            success("ffmpeg installed via winget.")
            return
    except Exception as e:
        warn("winget failed: " + str(e))

    info("Falling back to GitHub release...")
    try:
        import urllib.request as _ur, zipfile, tempfile
        api = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
        prx = _get_current_proxy()
        opener = _ur.build_opener()
        if prx:
            opener.add_handler(_ur.ProxyHandler({"http": prx, "https": prx}))
        with opener.open(api, timeout=20) as resp:
            import json as _jj
            data = _jj.loads(resp.read())
        assets = data.get("assets", [])
        url = next((a["browser_download_url"] for a in assets
                    if "essentials_build" in a["name"] and a["name"].endswith(".zip")), None)
        if not url:
            error("Could not find ffmpeg release asset.")
            return
        dest_dir = Path(os.environ.get("LOCALAPPDATA","~")).expanduser() / "ffmpeg"
        dest_dir.mkdir(parents=True, exist_ok=True)
        zip_path = dest_dir / "ffmpeg.zip"
        info("Downloading: " + url)
        with Progress(SpinnerColumn(spinner_name="dots"), TextColumn("{task.description}"),
                      BarColumn(complete_style="cyan bold", pulse_style="cyan"), DownloadColumn(), transient=True) as prog:
            task = prog.add_task("Downloading ffmpeg", total=None)
            with opener.open(url, timeout=120) as resp, open(zip_path, "wb") as fout:
                while True:
                    chunk = resp.read(65536)
                    if not chunk: break
                    fout.write(chunk)
                    prog.advance(task, len(chunk))
        info("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(dest_dir)
        zip_path.unlink(missing_ok=True)
        # find the bin folder
        bin_dirs = list(dest_dir.rglob("ffmpeg.exe"))
        if not bin_dirs:
            error("ffmpeg.exe not found after extraction.")
            return
        bin_dir = str(bin_dirs[0].parent)
        # add to user PATH
        cur = os.environ.get("PATH","")
        if bin_dir not in cur:
            new_path = cur.rstrip(";") + ";" + bin_dir
            subprocess.run(["powershell","-Command",
                "[System.Environment]::SetEnvironmentVariable('PATH','" +
                new_path.replace("'","''") + "','User')"], check=False)
            os.environ["PATH"] = new_path
        success("ffmpeg installed: " + bin_dir)
        success("Restart SmartDL for PATH to take effect.")
    except Exception as e:
        error("GitHub install failed: " + str(e))
        info("Manual install: https://ffmpeg.org/download.html")

def _install_wt():
    info("Installing Windows Terminal via winget...")
    try:
        r = subprocess.run(
            ["winget", "install", "--id", "Microsoft.WindowsTerminal", "-e",
             "--accept-source-agreements", "--accept-package-agreements"],
            timeout=180
        )
        if r.returncode == 0:
            success("Windows Terminal installed.")
        else:
            warn("winget returned non-zero. Check Microsoft Store manually.")
    except FileNotFoundError:
        error("winget not found. Install App Installer from Microsoft Store.")
    except Exception as e:
        error("Install failed: " + str(e))

def _relaunch_in_wt():
    import shutil as _sh2, tempfile
    python_exe = sys.executable
    script     = os.path.abspath(__file__)
    pid        = os.getpid()
    _py_launcher = _sh2.which("py") or _sh2.which("python") or python_exe
    py_q  = '"' + _py_launcher + '"'
    sc_q  = '"' + script + '"'
    cur_path = os.environ.get("PATH","")
    new_path = cur_path
    bat_lines = [
        "@echo off",
        f"set PATH={new_path}",
        f":wait",
        f"timeout /t 1 /nobreak >nul",
        f"tasklist /fi \"PID eq {pid}\" 2>nul | find \"{pid}\" >nul 2>&1",
        f"if not errorlevel 1 goto wait",
        f"timeout /t 1 /nobreak >nul",
        f"where wt >nul 2>&1",
        f"if not errorlevel 1 (",
        f"    start \"SmartDL\" wt new-tab {py_q} {sc_q}",
        f") else (",
        f"    start \"SmartDL\" cmd /k {py_q} {sc_q}",
        f")",
        f"(goto) 2>nul & del /f /q \"%~f0\"",
    ]
    bat_content = "\r\n".join(bat_lines)
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".bat", delete=False,
                                      encoding="utf-8", dir=tempfile.gettempdir())
    tf.write(bat_content); tf.close()
    subprocess.Popen(["cmd","/c", tf.name],
                     creationflags=subprocess.DETACHED_PROCESS|
                                   subprocess.CREATE_NEW_PROCESS_GROUP)
    info("Relaunching in Windows Terminal...")
    time.sleep(1)
    sys.exit(0)

# ─── Proxy step ───────────────────────────────────────────────────────────────
def _proxy_step():
    current = _get_current_proxy()
    if current:
        console.print()
        body = "[bold green]  Active proxy:[/bold green] [cyan]" + current + "[/cyan]\n  [dim]Press [bold]P[/bold] to change / clear   or   Enter to continue[/dim]"
        console.print(Panel(body, border_style="green", padding=(0,2)))
        while True:
            ch = Prompt.ask("  [bold yellow]> (Enter / p)[/bold yellow]", default="").strip().lower()
            if ch in ("", "p"):
                break
            warn("Invalid input \u2014 press Enter to continue or P to change proxy.")
        if ch == "p":
            _proxy_menu()
    else:
        console.print()
        console.print(Panel("[dim]No proxy configured.[/dim]\n  Press [bold cyan]P[/bold cyan] to set a proxy   or   [bold]Enter[/bold] to skip", border_style="dim", title="[dim]Proxy[/dim]", padding=(0,2)))
        while True:
            ch = Prompt.ask("  [bold yellow]> (Enter / p)[/bold yellow]", default="").strip().lower()
            if ch in ("", "p"):
                break
            warn("Invalid input \u2014 press Enter to skip or P to set proxy.")
        if ch == "p":
            _proxy_menu()

# ─── Output folder ────────────────────────────────────────────────────────────
def _pick_output_folder():
    default = Path.home() / "Downloads" / "SmartDL"
    console.print()
    console.print(Panel(
        "[dim]  Default folder:[/dim]\n    [bold cyan]" + str(default) + "[/bold cyan]\n\n"
        "    Press [bold]Enter[/bold] to accept the default\n"
        "    or type a new path to change it.",
        title="[bold]  Output Folder[/bold]", border_style="white", padding=(0,2)
    ))
    while True:
        raw = Prompt.ask("  [bold]📁 Path[/bold]", default=str(default)).strip()
        p = Path(raw)
        try:
            p.mkdir(parents=True, exist_ok=True)
            files = list(p.iterdir())
            if files:
                info("Folder exists \u2014 " + str(len(files)) + " file(s) inside")
            success("Output folder: " + str(p))
            return p
        except Exception as e:
            error("Cannot use that folder: " + str(e))

# ─── YouTube ──────────────────────────────────────────────────────────────────
def _get_yt_formats(url):
    ydl_opts = {"quiet": True, "no_warnings": True, "listformats": False, "noplaylist": True}
    prx = _get_current_proxy()
    if prx:
        ydl_opts["proxy"] = prx
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        err_s = str(e)
        # proxy unreachable → offer to clear and retry without proxy
        if prx and ("Unable to connect to proxy" in err_s or "10061" in err_s or "ProxyError" in err_s):
            warn("Proxy unreachable: " + prx)
            ans = Prompt.ask(
                "  [bold yellow]Clear proxy and retry without it?[/bold yellow] [dim](y / n)[/dim]",
                default="y"
            ).strip().lower()
            if ans != "n":
                _clear_proxy()
                info("Retrying without proxy...")
                with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                                       "listformats": False, "noplaylist": True}) as ydl:
                    return ydl.extract_info(url, download=False)
        raise

# ─── YouTube: info panel ──────────────────────────────────────────────────────
def _show_yt_info(info_dict):
    title   = info_dict.get("title", "?")
    channel = info_dict.get("uploader") or info_dict.get("channel") or "?"
    dur     = fmt_dur(info_dict.get("duration"))
    views   = info_dict.get("view_count")
    views_s = "{:,}".format(views) if views else "?"
    body = (
        "[bold white]" + title + "[/bold white]\n"
        "[dim]Channel:[/dim] [cyan]" + channel + "[/cyan]   "
        "[dim]Duration:[/dim] [green]" + dur + "[/green]   "
        "[dim]Views:[/dim] [yellow]" + views_s + "[/yellow]"
    )
    console.print(Panel(body, border_style="cyan", title="[bold]Video Info[/bold]", padding=(0,2)))

def _yt_quality_menu(info_dict) -> tuple:
    _show_yt_info(info_dict)
    fmts = info_dict.get("formats", [])
    ff   = _has_ffmpeg()

    combos     = sorted(
        [f for f in fmts if f.get("vcodec","none") != "none" and f.get("acodec","none") != "none"],
        key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)
    video_only = sorted(
        [f for f in fmts if f.get("vcodec","none") != "none" and f.get("acodec","none") == "none"],
        key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)
    audio_only = sorted(
        [f for f in fmts if f.get("vcodec","none") == "none" and f.get("acodec","none") != "none"],
        key=lambda x: x.get("abr") or 0, reverse=True)

    options = []
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta",
                  border_style="dim", padding=(0,1))
    table.add_column("#",       style="bold cyan",  width=4, justify="right")
    table.add_column("Type",    width=16)
    table.add_column("Quality", style="bold green", width=13)
    table.add_column("Format",  style="yellow",     width=7)
    table.add_column("Size",    style="blue",        width=12)
    table.add_column("Codec",   style="dim",         width=22)

    for f in combos[:6]:
        h  = f.get("height","?"); fps = f.get("fps","")
        q  = str(h) + "p" + ("@" + str(fps) + "fps" if fps else "") if h != "?" else "?"
        sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        vc = (f.get("vcodec") or "")[:10]; ac = (f.get("acodec") or "")[:8]
        idx = len(options)+1; options.append(("combined", f["format_id"]))
        table.add_row(str(idx), "\U0001f3ac Video+Audio", q, f.get("ext","?"), sz, vc+"+"+ac)

    for h in [2160,1440,1080,720,480,360,240,144]:
        m = [f for f in video_only if f.get("height") == h]
        if not m: continue
        f = m[0]; fps = f.get("fps","")
        sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        vc = (f.get("vcodec") or "")[:10]
        idx = len(options)+1; options.append(("merge", h))
        needs = "" if ff else " [dim](needs ffmpeg)[/dim]"
        table.add_row(str(idx), "[bold]\U0001f4fa Video HD[/bold]",
                      str(h)+"p"+("@"+str(fps)+"fps" if fps else ""), "mp4",
                      (sz+"+" if sz != "?" else "?"), vc+"+bestaudio"+needs)

    for f in audio_only[:4]:
        abr = f.get("abr","?")
        q   = str(abr) + " kbps" if abr != "?" else f.get("format_note","?")
        sz  = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        idx = len(options)+1; options.append(("audio", f["format_id"]))
        table.add_row(str(idx), "[green]\U0001f3b5 Audio Only[/green]", q,
                      (f.get("ext") or "?"), sz, (f.get("acodec") or "")[:20])

    for label, kind, fmt_id in [
        ("\U0001f3c6 Best Quality (auto)", "best_v", "bestvideo+bestaudio/best"),
        ("\U0001f399 Audio MP3 192k",      "best_a", "bestaudio/best"),
    ]:
        idx = len(options)+1; options.append((kind, fmt_id))
        table.add_row(str(idx), label, "auto", "auto", "?", "yt-dlp auto")

    console.print(table)
    if not ff:
        warn("ffmpeg not found \u2014 Video HD rows need it for merging.  "
             "Type [bold]i[/bold] at URL prompt to install.")

    while True:
        try:
            choice = IntPrompt.ask("  [bold yellow]Select quality #[/bold yellow]",
                               default=len(options)-1)
        except (KeyboardInterrupt, EOFError):
            return None, False
        choice = max(1, min(choice, len(options)))
        kind, val = options[choice-1]
        if not ff and kind in ("merge", "best_v"):
            warn("This format requires ffmpeg. Type [bold]i[/bold] to install it.")
            continue
        if kind == "combined": return val, False
        if kind == "merge":    return "bestvideo[height<=" + str(val) + "]+bestaudio/best", False
        if kind == "audio":    return val, False
        if kind == "best_v":   return val, False
        if kind == "best_a":   return val, True
        return "bestvideo+bestaudio/best", False

def _download_yt(url, out_folder, fmt, is_audio=False):
    stop_event.clear()
    prx   = _get_current_proxy()
    maxr  = DL_SETTINGS["max_retries"]
    frags = DL_SETTINGS["fragments"]
    retry_label = "infinite" if maxr >= 999 else str(maxr)
    print_section("Downloading", "\u2b07")
    info("Resume enabled  \u00b7  " + retry_label + " retr" + ("y" if maxr==1 else "ies") +
         "  \u00b7  " + str(frags) + "-thread fragments")

    opts = {
        "format":                        fmt,
        "outtmpl":                       str(out_folder / "%(title)s [%(format_id)s].%(ext)s"),
        "continuedl":                    True,
        "retries":                       maxr,
        "fragment_retries":              maxr,
        "skip_unavailable_fragments":    False,
        "concurrent_fragment_downloads": frags,
        "socket_timeout":                30,
        "http_chunk_size":               10 * 1024 * 1024,
        "logger":                        YTLogger(),
        "progress_hooks":                [yt_hook],
        "merge_output_format":           "mp4" if (not is_audio and "+" in fmt) else None,
        "quiet":                         True,
        "no_progress":                   True,
        "file_access_retries":           10,
        "extractor_retries":             10,
        "postprocessors": (
            [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
            if is_audio else []
        ),
    }
    if prx:
        opts["proxy"] = prx

    def _do_download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    with make_progress() as prog:
        _progress_ctx["last"] = 0
        _progress_ctx["task"] = prog.add_task("[cyan]Downloading...[/cyan]", total=None)
        _progress_ctx["obj"]  = prog
        try:
            retry_with_backoff(_do_download, max_retries=maxr)
        except KeyboardInterrupt:
            warn("Stopped by user.")
            return
        except Exception as e:
            if stop_event.is_set(): return
            err_s = str(e)
            prx2  = _get_current_proxy()
            if prx2 and ("Unable to connect to proxy" in err_s or "10061" in err_s):
                warn("Proxy unreachable: " + prx2)
                ans = Prompt.ask(
                    "  [bold yellow]Clear proxy and retry?[/bold yellow] [dim](y / n)[/dim]",
                    default="y").strip().lower()
                if ans != "n":
                    _clear_proxy()
                    opts.pop("proxy", None)
                    try:
                        with make_progress() as prog2:
                            _progress_ctx["last"] = 0
                            _progress_ctx["task"] = prog2.add_task("[cyan]Downloading...[/cyan]", total=None)
                            _progress_ctx["obj"]  = prog2
                            retry_with_backoff(_do_download, max_retries=maxr)
                        success("Download complete!  \u2192  " + str(out_folder))
                        return
                    except Exception as e2:
                        error(str(e2)[:200])
                        hint = _diagnose_error(e2)
                        if hint: info(hint)
                        return
            error(str(e)[:200])
            hint = _diagnose_error(e)
            if hint: info(hint)
            return
        finally:
            _progress_ctx["task"] = None
            _progress_ctx["obj"]  = None

    success("Download complete!  \u2192  " + str(out_folder))

# ─── Podcast / direct ─────────────────────────────────────────────────────────
def _is_rss(text):
    return "<rss" in text[:2000] or "<feed" in text[:2000]

def _parse_rss(text):
    items = []
    for block in re.findall(r'<item[^>]*>(.*?)</item>', text, re.DOTALL):
        title_m = re.search(r'<title[^>]*><!\[CDATA\[(.+?)\]\]>|<title[^>]*>([^<]+)<', block)
        enc_m   = re.search(r'<enclosure[^>]+url=["\'"]([^"\']+)["\'"][^>]*/?>|<enclosure[^>]+url=([^\s>]+)', block)
        title   = (title_m.group(1) or title_m.group(2)).strip() if title_m else "Episode"
        url     = (enc_m.group(1) or enc_m.group(2)).strip() if enc_m else None
        if url: items.append((title, url))
    return items

def _podcast_quality_menu():
    print_section("Quality \u2014 podcast", "\u2699")
    rows = [
        ("Original (no conversion)", "original", "Direct \u2014 fastest"),
        ("MP3  192 kbps",            "mp3",      "Good quality \u2014 requires ffmpeg"),
        ("MP3  128 kbps",            "mp3_128",  "Smaller file"),
        ("MP3  320 kbps",            "mp3_320",  "Highest MP3 quality"),
        ("M4A (AAC) 128k",           "m4a",      "Best for Apple"),
        ("OGG  192 kbps",            "ogg",      "Open format"),
    ]
    needs_ff = ["mp3","mp3_128","mp3_320","m4a","ogg"]
    t = Table(box=box.ROUNDED, show_header=True, border_style="cyan", padding=(0,1))
    t.add_column("#",       style="bold cyan", width=5,  justify="right")
    t.add_column("Quality", style="white",     width=23)
    t.add_column("Format",  style="dim",       width=9)
    t.add_column("Size",    style="dim",       width=14)
    t.add_column("Note",    style="dim",       width=31)
    for i,(label,fmt,note) in enumerate(rows,1):
        sz = "converted" if fmt in needs_ff else "?"
        t.add_row(str(i), label, fmt.split("_")[0], sz, note)
    console.print(t)
    if not _has_ffmpeg():
        warn("Conversion options require ffmpeg")
        info("Type [bold]i[/bold] at the URL prompt to install ffmpeg from within SmartDL.")
    while True:
        try:
            sel = Prompt.ask("  [bold yellow]Select quality #[/bold yellow]", default="1").strip()
        except (KeyboardInterrupt, EOFError):
            return None, False
        if sel.isdigit() and 1 <= int(sel) <= len(rows):
            return rows[int(sel)-1]
        warn("Enter a number between 1 and " + str(len(rows)) + ".")

def _convert_audio(raw_path, out_path, fmt_key):
    bitrate_map = {"mp3":"192k","mp3_128":"128k","mp3_320":"320k","m4a":"128k","ogg":"192k"}
    ext_map     = {"mp3":"mp3","mp3_128":"mp3","mp3_320":"mp3","m4a":"m4a","ogg":"ogg"}
    bitrate = bitrate_map.get(fmt_key,"192k")
    ext     = ext_map.get(fmt_key,"mp3")
    final   = out_path.with_suffix("." + ext)
    with Progress(SpinnerColumn(spinner_name="dots"), TextColumn("{task.description}"), BarColumn(complete_style="cyan bold", pulse_style="cyan"),
                  transient=True, console=console) as prog:
        prog.add_task("Converting to " + ext.upper() + "...", total=None)
        subprocess.check_call(
            ["ffmpeg","-y","-i",str(raw_path),"-b:a",bitrate,str(final)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    return final

def _download_podcast_url(url, out_folder, fmt_tuple):
    stop_event.clear()
    label, fmt_key, _ = fmt_tuple
    prx = _get_current_proxy()
    max_r = DL_SETTINGS["max_retries"]
    frags = DL_SETTINGS["fragments"]
    retry_label = "infinite" if max_r >= 999 else str(max_r)

    print_section("Downloading", "\u2193")
    info("Resume enabled  \u00b7  " + retry_label + " retr" + ("y" if max_r==1 else "ies") +
         "  \u00b7  " + str(frags) + "-thread fragments")

    ydl_opts = {
        "outtmpl":         str(out_folder / "podcast_raw"),
        "quiet":           True,
        "no_warnings":     True,
        "continuedl":      True,
        "retries":         max_r,
        "fragment_retries":max_r,
        "concurrent_fragment_downloads": frags,
        "noprogress":      True,
    }
    if prx: ydl_opts["proxy"] = prx

    raw = out_folder / "podcast_raw"
    attempt = 0
    while not stop_event.is_set():
        attempt += 1
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # pick the actual downloaded file (yt-dlp may add extension)
            candidates = list(out_folder.glob("podcast_raw*"))
            raw = candidates[0] if candidates else raw

            if fmt_key == "original":
                out = out_folder / ("podcast." + raw.suffix.lstrip(".") or "mp3")
                raw.rename(out)
                success("Downloaded: " + out.name)
            else:
                if not _has_ffmpeg():
                    error("ffmpeg not found. Install it first (type i at URL prompt).")
                    warn("Raw file saved: " + str(raw))
                    return
                out = out_folder / "podcast"
                try:
                    final = _convert_audio(raw, out, fmt_key)
                    raw.unlink(missing_ok=True)
                    success("Downloaded: " + final.name)
                except Exception as e:
                    _estr = str(e)
                    if "3199971767" in _estr or "BEF00007" in _estr.upper():
                        error("ffmpeg could not convert \u2014 file may be DRM-protected or corrupted.")
                        info("Spotify tracks are DRM-protected and cannot be converted.")
                        info("Try a different source, or use option 1 (Original) to keep the raw file.")
                    else:
                        error("ffmpeg error: " + _estr)
                    warn("Raw file saved: " + str(raw))
            return

        except KeyboardInterrupt:
            warn("Stopped by user.")
            return
        except Exception as e:
            if stop_event.is_set(): return
            warn("[" + str(attempt) + "] Error: " + str(e)[:120])
            time.sleep(min(attempt * 2, 30))

def _handle_podcast(url, out_folder):
    print_section("Analyzing podcast link", "\U0001f3a4")
    prx = _get_current_proxy()
    try:
        s = requests.Session()
        if prx:
            s.proxies = {"http": prx, "https": prx}
        resp = s.get(url, timeout=15, allow_redirects=True,
                     headers={"User-Agent":"Mozilla/5.0"})
        ct   = resp.headers.get("Content-Type","")
        text = resp.text

        # RSS feed
        if "xml" in ct or "rss" in ct or _is_rss(text):
            items = _parse_rss(text)
            if not items:
                error("RSS feed found but no episodes.")
                return
            t = Table(box=box.ROUNDED, show_header=True, border_style="cyan", padding=(0,1))
            t.add_column("#",     style="bold cyan", width=5, justify="right")
            t.add_column("Title", style="white")
            for i,(title,_) in enumerate(items[:20],1):
                t.add_row(str(i), title[:70])
            console.print(t)
            while True:
                sel = Prompt.ask("  [bold yellow]Episode #[/bold yellow]", default="1").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(items[:20]):
                    _, ep_url = items[int(sel)-1]
                    break
                warn("Invalid selection.")
            fmt = _podcast_quality_menu()
            _download_podcast_url(ep_url, out_folder, fmt)
            return

        # direct audio
        if "audio" in ct or url.lower().endswith((".mp3",".m4a",".ogg",".opus",".flac",".wav")):
            fmt = _podcast_quality_menu()
            _download_podcast_url(url, out_folder, fmt)
            return

    except Exception:
        pass

    # fallback: yt-dlp
    try:
        ydl_opts = {"quiet":True,"no_warnings":True}
        if prx: ydl_opts["proxy"] = prx
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
        fmt = _podcast_quality_menu()
        _download_podcast_url(url, out_folder, fmt)
    except Exception as e:
        error("Cannot handle this URL: " + str(e)[:120])

# ─── Main loop ────────────────────────────────────────────────────────────────
def main():
    print_header()

    console.print(Panel(
        "\n"
        "  [bold cyan]YouTube[/bold cyan]        Video or playlist URL \u2192 choose video/audio quality\n"
        "  [bold cyan]Podcast[/bold cyan]        Direct MP3 link | RSS feed | SoundCloud | ...\n"
        "  [bold cyan]Stop[/bold cyan]           Ctrl+C \u2014 partial file is saved and resumable\n"
        "  [bold cyan]P / p[/bold cyan]          Open proxy settings at any URL prompt\n"
        "  [bold cyan]S / s[/bold cyan]          Open download settings (retries, fragment threads)\n"
        "\n",
        title="[bold]  Quick Guide[/bold]", border_style="white", padding=(0,2)
    ))

    try:
        out_folder = _pick_output_folder()
        _proxy_step()
    except (KeyboardInterrupt, EOFError):
        _bye()
        return

    while True:
        stop_event.clear()
        console.print()
        console.print(Rule(style="dim"))
        console.print()
        try:
            url = Prompt.ask(
                "  [bold cyan]\U0001f517 URL[/bold cyan] "
                "[dim](q = quit  \u00b7  p = proxy  \u00b7  s = settings  \u00b7  i = install)[/dim]"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            _bye()
            return
            
        if url.lower() == "q":
            _bye()
            break

        if url.lower() == "p":
            _proxy_menu()
            continue

        if url.lower() == "s":
            _settings_menu()
            continue

        if url.lower() == "i":
            _install_menu()
            continue

        if not url.startswith(("http://","https://","ftp://")):
            warn("Not a valid URL. Start with http:// or https://")
            continue

        try:
            if is_youtube_url(url):
                print_section("Analyzing YouTube link", "\U0001f3a5")
                info_dict = _get_yt_formats(url)
                if not info_dict:
                    error("Could not fetch video info.")
                    continue
                fmt, is_audio = _yt_quality_menu(info_dict)
                if fmt is None:
                    continue
                if is_audio and not _has_ffmpeg():
                    _warn_no_ffmpeg("convert to MP3")
                    continue
                _download_yt(url, out_folder, fmt, is_audio)

            else:
                _handle_podcast(url, out_folder)
        except KeyboardInterrupt:
            warn("Interrupted.")
        except Exception as e:
            error("Unexpected error: " + str(e))
            traceback.print_exc()
            
        console.print()
        while True:
            try:
                again = Prompt.ask(
                    " [bold yellow]Download another?[/bold yellow] [dim](y / n)[/dim]",
                    default="y"
                ).strip().lower()
            except (KeyboardInterrupt, EOFError):
                _bye()
                return
            if again in ("", "y", "n"):
                break
            warn("Please enter y or n.")
        if again == "n":
            _bye()
            break

if __name__ == "__main__":
    main()
