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
\___ \| '_ ` _ \ / _` | '__| __| | | | |
 ___) | | | | | | (_| | |  | |_| |_| | |___
|____/|_| |_| |_|\__,_|_|   \__|____/|_____|
"""
VERSION = "2.2.1"

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
    console.print(Align(Text("v" + VERSION + "  \u00b7  Smart YouTube & Podcast Downloader  \u00b7  Ctrl+C to stop", style="dim"), align="center"))
    console.print(Align(Text("by Hellch!ef  \u00b7  if u know u know", style="dim italic"), align="center"))
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
        (10808, "v2rayN / Xray  (SOCKS5 default)"),
        (10809, "v2rayN / Xray  (HTTP default)"),
        (7890,  "Clash for Windows"),
        (1080,  "Generic SOCKS5"),
        (8080,  "Generic HTTP"),
        (3128,  "Squid / generic HTTP"),
    ]
    while True:
        console.print()
        t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
        t.add_column(style="bold cyan", width=4, justify="right")
        t.add_column(style="white")
        t.add_column(style="dim")
        t.add_row("1", "Enter proxy address manually", "(http://host:port or socks5://host:port)")
        t.add_row("2", "Use localhost", "(Proxifier / Clash / v2ray common ports)")
        t.add_row("3", "Paste v2ray share link", "(vmess:// \u00b7 vless:// \u00b7 trojan:// \u00b7 ss://)")
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
            console.print(t2)
            sel = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="2").strip().lower()
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
            link = Prompt.ask("  [bold yellow]v2ray link[/bold yellow]").strip()
            addr = _parse_v2ray_link(link)
            if addr:
                _apply_proxy(addr); success("Proxy set from v2ray link: " + addr)
            else:
                error("Could not parse link. Use manual entry instead.")
            break

        elif ch == "4":
            _clear_proxy(); success("Proxy cleared.")
            break
        else:
            warn("Invalid selection.")

def _parse_v2ray_link(link: str) -> str:
    import base64 as _b64
    link = link.strip()
    try:
        if link.startswith("vmess://"):
            raw = link[8:]
            pad = (-len(raw)) % 4
            decoded = _b64.b64decode(raw + "=" * pad).decode("utf-8")
            import json as _j
            cfg = _j.loads(decoded)
            host = cfg.get("add","127.0.0.1")
            port = cfg.get("port", 10809)
            return "http://" + str(host) + ":" + str(port)
        elif link.startswith(("vless://","trojan://")):
            rest = link.split("://",1)[1]
            hostport = rest.split("@",1)[-1].split("?")[0].split("/")[0]
            return "http://" + hostport
        elif link.startswith("ss://"):
            rest = link[5:]
            if "@" in rest:
                hostport = rest.split("@",1)[1].split("/")[0].split("#")[0]
            else:
                pad = (-len(rest)) % 4
                decoded = _b64.b64decode(rest + "=" * pad).decode()
                hostport = decoded.split("@",1)[-1] if "@" in decoded else decoded.split(":",1)[1]
            return "http://" + hostport
    except Exception:
        pass
    return ""

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
        with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                      BarColumn(), DownloadColumn(), transient=True) as prog:
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
    ydl_opts = {"quiet":True,"no_warnings":True,"listformats":False,"noplaylist":True}
    prx = _get_current_proxy()
    if prx: ydl_opts["proxy"] = prx
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def _yt_quality_menu(info_dict):
    title    = info_dict.get("title","Unknown")
    duration = fmt_dur(info_dict.get("duration"))
    fmts     = info_dict.get("formats", [])

    # separate video+audio combos and audio-only
    combos, audio_only = [], []
    for f in fmts:
        vcodec = f.get("vcodec","none")
        acodec = f.get("acodec","none")
        if vcodec not in (None,"none") and acodec not in (None,"none"):
            combos.append(f)
        elif vcodec in (None,"none") and acodec not in (None,"none"):
            audio_only.append(f)

    # group combos by height
    by_height = {}
    for f in combos:
        h = f.get("height") or 0
        if h not in by_height or (f.get("filesize") or 0) > (by_height[h].get("filesize") or 0):
            by_height[h] = f
    video_rows = sorted(by_height.values(), key=lambda x: x.get("height") or 0, reverse=True)

    # best audio only
    best_audio = max(audio_only, key=lambda f: f.get("abr") or 0) if audio_only else None

    rows = []
    for f in video_rows:
        h     = f.get("height") or 0
        fps   = f.get("fps") or ""
        vcodec= f.get("vcodec","").split(".")[0]
        acodec= f.get("acodec","").split(".")[0]
        sz    = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        label = str(h) + "p" + (" " + str(fps) + "fps" if fps else "")
        rows.append({"label":label,"fmt_id":f["format_id"],"size":sz,
                     "note":vcodec + "+" + acodec,"type":"video"})
    if best_audio:
        abr  = best_audio.get("abr") or "?"
        ac   = best_audio.get("acodec","").split(".")[0]
        sz   = fmt_size(best_audio.get("filesize") or best_audio.get("filesize_approx"))
        rows.append({"label":"Audio only  " + str(abr) + " kbps",
                     "fmt_id":best_audio["format_id"],"size":sz,"note":ac,"type":"audio"})

    print_section("Quality \u2014 " + title[:50], "\u2699")
    info("Duration: " + duration)
    t = Table(box=box.ROUNDED, show_header=True, border_style="cyan", padding=(0,1))
    t.add_column("#",       style="bold cyan", width=5,  justify="right")
    t.add_column("Quality", style="white",     width=18)
    t.add_column("Size",    style="dim",       width=10)
    t.add_column("Codecs",  style="dim",       width=14)
    for i,r in enumerate(rows,1):
        t.add_row(str(i), r["label"], r["size"], r["note"])
    console.print(t)

    while True:
        sel = Prompt.ask("  [bold yellow]Select quality #[/bold yellow]", default="1").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(rows):
            return rows[int(sel)-1]
        warn("Enter a number between 1 and " + str(len(rows)) + ".")

def _download_yt(url, out_folder, fmt):
    stop_event.clear()
    prx = _get_current_proxy()
    max_r = DL_SETTINGS["max_retries"]
    frags = DL_SETTINGS["fragments"]
    retry_label = "infinite" if max_r >= 999 else str(max_r)

    print_section("Downloading", "\u2b07")
    info("Resume enabled  \u00b7  " + retry_label + " retr" + ("y" if max_r==1 else "ies") +
         "  \u00b7  " + str(frags) + "-thread fragments")

    class _Hook:
        def __init__(self):
            self.prog  = None
            self.task  = None
            self.total = None
            self._ctx  = None
        def __call__(self, d):
            if stop_event.is_set(): raise KeyboardInterrupt
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if self.prog is None:
                    self._ctx = Progress(
                        SpinnerColumn(),
                        TextColumn("{task.description}"),
                        BarColumn(bar_width=40),
                        DownloadColumn(),
                        TransferSpeedColumn(),
                        TimeRemainingColumn(),
                        console=console, transient=False
                    )
                    self.prog = self._ctx.__enter__()
                    self.task = self.prog.add_task("Downloading", total=total)
                    self.total = total
                elif total and self.total != total:
                    self.prog.update(self.task, total=total)
                    self.total = total
                self.prog.update(self.task, completed=downloaded)
            elif d["status"] == "finished":
                if self.prog:
                    self.prog.update(self.task, completed=self.total or 1)
                    self._ctx.__exit__(None,None,None)
                    self.prog = None

    hook = _Hook()
    ydl_opts = {
        "format":          fmt["fmt_id"],
        "outtmpl":         str(out_folder / "%(title)s.%(ext)s"),
        "progress_hooks":  [hook],
        "quiet":           True,
        "no_warnings":     True,
        "continuedl":      True,
        "retries":         max_r,
        "fragment_retries":max_r,
        "concurrent_fragment_downloads": frags,
        "noprogress":      True,
    }
    if prx: ydl_opts["proxy"] = prx

    attempt = 0
    while not stop_event.is_set():
        attempt += 1
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            success("Download complete!  \u2192  " + str(out_folder))
            return
        except KeyboardInterrupt:
            warn("Stopped by user.")
            return
        except Exception as e:
            if stop_event.is_set(): return
            err_s = str(e)
            warn("[" + str(attempt) + "] Error: " + err_s[:120])
            if "Sign in" in err_s or "bot" in err_s.lower():
                error("YouTube requires sign-in or bot check \u2014 try a different URL.")
                return
            time.sleep(min(attempt * 2, 30))

# ─── Podcast / direct ─────────────────────────────────────────────────────────
def _is_rss(text):
    return "<rss" in text[:2000] or "<feed" in text[:2000] or "<channel>" in text[:2000]

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
        sel = Prompt.ask("  [bold yellow]Select quality #[/bold yellow]", default="1").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(rows):
            return rows[int(sel)-1]
        warn("Enter a number between 1 and " + str(len(rows)) + ".")

def _convert_audio(raw_path, out_path, fmt_key):
    bitrate_map = {"mp3":"192k","mp3_128":"128k","mp3_320":"320k","m4a":"128k","ogg":"192k"}
    ext_map     = {"mp3":"mp3","mp3_128":"mp3","mp3_320":"mp3","m4a":"m4a","ogg":"ogg"}
    bitrate = bitrate_map.get(fmt_key,"192k")
    ext     = ext_map.get(fmt_key,"mp3")
    final   = out_path.with_suffix("." + ext)
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
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

    print_section("Downloading", "\u2b07")
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

    out_folder = _pick_output_folder()
    _proxy_step()

    while True:
        stop_event.clear()
        console.print()
        console.print(Rule(style="dim"))
        console.print()
        url = Prompt.ask(
            "  [bold cyan]\U0001f517 URL[/bold cyan] "
            "[dim](q = quit  \u00b7  p = proxy  \u00b7  s = settings  \u00b7  i = install)[/dim]"
        ).strip()

        if url.lower() == "q":
            console.print()
            console.print(Align(Text("bye \u2764", style="bold cyan"), align="center"))
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
                fmt = _yt_quality_menu(info_dict)
                _download_yt(url, out_folder, fmt)
            else:
                _handle_podcast(url, out_folder)
        except KeyboardInterrupt:
            warn("Interrupted.")
        except Exception as e:
            error("Unexpected error: " + str(e))
            traceback.print_exc()

if __name__ == "__main__":
    main()
