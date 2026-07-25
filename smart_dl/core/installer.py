"""Dependency installer — ffmpeg, Node.js, Windows Terminal."""
import os
import subprocess
import sys
import time
from pathlib import Path

from rich import box
from rich.panel import Panel
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from smart_dl.ui import console, error, info, success, warn


def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg","-version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def has_nodejs():
    import shutil
    return bool(shutil.which("node"))


def _install_ffmpeg():
    import shutil

    from smart_dl.core.proxy import get_current_proxy
    info("Trying winget...")
    try:
        r = subprocess.run(
            ["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements",
             "--accept-package-agreements"],
            timeout=180
        )
        if r.returncode == 0 and shutil.which("ffmpeg"):
            success("ffmpeg installed via winget.")
            return
    except Exception as e:
        warn("winget failed: " + str(e))

    info("Falling back to GitHub release...")
    try:
        import urllib.request as _ur
        import zipfile
        api = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
        prx = get_current_proxy()
        opener = _ur.build_opener()
        if prx:
            opener.add_handler(_ur.ProxyHandler({"http": prx, "https": prx}))
        with opener.open(api, timeout=20) as resp:
            import json
            data = json.loads(resp.read())
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
        bin_dirs = list(dest_dir.rglob("ffmpeg.exe"))
        if not bin_dirs:
            error("ffmpeg.exe not found after extraction.")
            return
        bin_dir = str(bin_dirs[0].parent)
        cur = os.environ.get("PATH","")
        if bin_dir not in cur:
            new_path = cur.rstrip(";") + ";" + bin_dir
            ps_script = (
                "[System.Environment]::SetEnvironmentVariable('PATH', $args[0], 'User')"
            )
            subprocess.run(
                ["powershell", "-Command", ps_script, new_path],
                check=False
            )
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
    import shutil
    import tempfile
    python_exe = sys.executable
    script     = os.path.abspath(__file__)
    pid        = os.getpid()
    _py_launcher = shutil.which("py") or shutil.which("python") or python_exe
    py_q  = '"' + _py_launcher + '"'
    sc_q  = '"' + script + '"'
    cur_path = os.environ.get("PATH","")
    new_path = cur_path
    bat_lines = [
        "@echo off",
        f"set PATH={new_path}",
        ":wait",
        "timeout /t 1 /nobreak >nul",
        f"tasklist /fi \"PID eq {pid}\" 2>nul | find \"{pid}\" >nul 2>&1",
        "if not errorlevel 1 goto wait",
        "timeout /t 1 /nobreak >nul",
        "where wt >nul 2>&1",
        "if not errorlevel 1 (",
        f"    start \"SmartDL\" wt new-tab {py_q} {sc_q}",
        ") else (",
        f"    start \"SmartDL\" cmd /k {py_q} {sc_q}",
        ")",
        "(goto) 2>nul & del /f /q \"%~f0\"",
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


def fix_youtube_deps():
    """Interactive menu to update yt-dlp and install Node.js."""
    has_node = has_nodejs()
    try:
        import importlib.metadata as _im
        ytdlp_ver = _im.version("yt-dlp")
    except Exception:
        ytdlp_ver = "unknown"

    console.print()
    console.print(Panel(
        "[bold yellow]  YouTube requires two things to work properly:[/bold yellow]\n\n"
        "  [bold]1.[/bold] [cyan]yt-dlp[/cyan] \u2014 up to date   "
        + ("[green](installed: " + ytdlp_ver + ")[/green]" if ytdlp_ver != "unknown" else "[red]unknown[/red]") + "\n"
        "  [bold]2.[/bold] [cyan]Node.js[/cyan] \u2014 for JS challenge solving   "
        + ("[green]\u2713 found[/green]" if has_node else "[red]\u2717 not found[/red]") + "\n\n"
        "  [dim]Without these, YouTube bot-detection cannot be bypassed.[/dim]",
        border_style="yellow",
        title="[bold yellow]  YouTube Fix[/bold yellow]",
        padding=(0, 2)
    ))

    t = Table(box=box.ROUNDED, show_header=False, border_style="yellow", padding=(0,2))
    t.add_column(style="bold yellow", width=4, justify="right")
    t.add_column(style="white")
    t.add_column(style="dim")
    t.add_row("1", "Update yt-dlp",   "pip install -U yt-dlp")
    if not has_node:
        t.add_row("2", "Install Node.js", "via winget  (recommended)")
    t.add_row("3", "Do both",         "recommended")
    t.add_row("0", "Skip", "")
    console.print(Panel(t, title="[bold yellow]  What would you like to do?[/bold yellow]",
                        border_style="yellow", padding=(0,1)))

    ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="3").strip()

    if ch in ("1", "3"):
        info("Updating yt-dlp...")
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "--quiet"],
                timeout=120
            )
            if r.returncode == 0:
                success("yt-dlp updated successfully.")
            else:
                warn("yt-dlp update may have failed.")
        except Exception as e:
            error("Failed to update yt-dlp: " + str(e))

    if (ch in ("2", "3")) and not has_node:
        info("Installing Node.js via winget...")
        try:
            r = subprocess.run(
                ["winget", "install", "--id", "OpenJS.NodeJS.LTS", "-e",
                 "--accept-source-agreements", "--accept-package-agreements"],
                timeout=300
            )
            if r.returncode == 0:
                success("Node.js installed. Restart SmartDL for it to take effect.")
            else:
                warn("winget install may have failed.")
                info("Manual install: https://nodejs.org")
        except FileNotFoundError:
            error("winget not found.")
            info("Install Node.js manually from: [bold cyan]https://nodejs.org[/bold cyan]")
        except Exception as e:
            error("Failed: " + str(e))

    if ch == "0":
        return


def install_menu():
    """Interactive dependency installation menu."""
    while True:
        has_ff = has_ffmpeg()
        try:
            import shutil
            has_wt = bool(shutil.which("wt"))
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
        t.add_row("3", "Fix YouTube bot detection", "(yt-dlp update + Node.js)")
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
            try:
                import shutil
                if shutil.which("wt"):
                    ans = Prompt.ask(
                        "  [bold yellow]Relaunch SmartDL inside Windows Terminal now?[/bold yellow]",
                        default="y"
                    ).strip().lower()
                    if ans == "y":
                        _relaunch_in_wt()
            except Exception:
                pass
        elif ch == "3":
            fix_youtube_deps()
        else:
            warn("Invalid selection.")
