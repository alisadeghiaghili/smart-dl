"""Torrent/magnet download support."""
import os
import sys
import subprocess
from pathlib import Path
from rich.panel import Panel
from rich.prompt import Prompt

from smart_dl.ui import console, success, warn, error, info, print_section
from smart_dl.core.proxy import get_current_proxy

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


def is_magnet_link(url: str) -> bool:
    """Check if URL is a magnet link."""
    return url.startswith("magnet:?xt=")


def is_torrent_file(path: str) -> bool:
    """Check if file is a .torrent file."""
    return path.lower().endswith(".torrent") and os.path.isfile(path)


def has_transmission() -> bool:
    """Check if transmission-cli is available."""
    try:
        subprocess.run(["transmission-cli", "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def has_aria2c() -> bool:
    """Check if aria2c is available."""
    try:
        subprocess.run(["aria2c", "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def has_qbittorrent() -> bool:
    """Check if qbittorrent-cli is available."""
    try:
        subprocess.run(["qbt", "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _get_available_client() -> str:
    """Find an available torrent client."""
    if has_aria2c():
        return "aria2c"
    if has_transmission():
        return "transmission"
    if has_qbittorrent():
        return "qbittorrent"
    return ""


def download_torrent(url: str, out_folder: Path):
    """Download a torrent/magnet link."""
    print_section("Downloading torrent", "\U0001f4e6")

    client = _get_available_client()

    if not client:
        console.print(Panel(
            "[bold yellow]No torrent client found![/bold yellow]\n\n"
            " SmartDL needs a torrent client to download. Install one of:\n\n"
            " [bold]1.[/bold] [cyan]aria2c[/cyan] (recommended)\n"
            "    winget install aria2.aria2\n\n"
            " [bold]2.[/bold] [cyan]transmission-cli[/cyan]\n"
            "    winget install Transmission.Transmission\n\n"
            " [bold]3.[/bold] [cyan]qBittorrent[/cyan]\n"
            "    winget install qBittorrent.qBittorrent\n",
            border_style="yellow",
            title="[bold yellow] Torrent Client Required[/bold yellow]",
            padding=(0, 2)
        ))

        # Offer to install aria2c
        ans = Prompt.ask(
            "  [bold yellow]Install aria2c now?[/bold yellow] [dim](y / n)[/dim]",
            default="y"
        ).strip().lower()
        if ans == "y":
            _install_aria2()
            client = _get_available_client()
            if not client:
                error("Could not install aria2c.")
                return
        else:
            return

    # Download
    out_dir = str(out_folder)

    if client == "aria2c":
        _download_aria2(url, out_dir)
    elif client == "transmission":
        _download_transmission(url, out_dir)
    elif client == "qbittorrent":
        _download_qbittorrent(url, out_dir)


def _install_aria2():
    """Install aria2c via winget."""
    info("Installing aria2c via winget...")
    try:
        r = subprocess.run(
            ["winget", "install", "--id", "aria2.aria2", "-e",
             "--accept-source-agreements", "--accept-package-agreements"],
            timeout=120
        )
        if r.returncode == 0:
            success("aria2c installed successfully.")
        else:
            warn("winget install may have failed.")
            info("Manual install: https://aria2.github.io/")
    except FileNotFoundError:
        error("winget not found. Install aria2c manually.")
    except Exception as e:
        error("Install failed: " + str(e))


def _download_aria2(url: str, out_dir: str):
    """Download using aria2c."""
    cmd = [
        "aria2c",
        "--dir=" + out_dir,
        "--continue=true",
        "--max-connection-per-server=16",
        "--split=16",
        "--min-split-size=1M",
        "--disk-cache=64M",
        "--file-allocation=none",
    ]

    prx = get_current_proxy()
    if prx:
        cmd.append("--all-proxy=" + prx)

    if is_magnet_link(url):
        cmd.append(url)
    else:
        cmd.append(url)

    info("Starting download with aria2c...")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            line = line.strip()
            if line:
                info(line[:100])
        proc.wait()
        if proc.returncode == 0:
            success("Torrent download complete!")
        else:
            error("aria2c exited with code " + str(proc.returncode))
    except KeyboardInterrupt:
        warn("Stopped by user.")
        proc.kill()
    except Exception as e:
        error("Download failed: " + str(e))


def _download_transmission(url: str, out_dir: str):
    """Download using transmission-cli."""
    cmd = ["transmission-cli", "-w", out_dir, url]
    info("Starting download with transmission-cli...")
    try:
        subprocess.run(cmd, timeout=None)
        success("Torrent download complete!")
    except KeyboardInterrupt:
        warn("Stopped by user.")
    except Exception as e:
        error("Download failed: " + str(e))


def _download_qbittorrent(url: str, out_dir: str):
    """Download using qBittorrent CLI."""
    cmd = ["qbt", "torrent", "add", url, "--save-path", out_dir]
    info("Starting download with qBittorrent...")
    try:
        subprocess.run(cmd, timeout=None)
        success("Torrent added to qBittorrent!")
    except Exception as e:
        error("Failed to add torrent: " + str(e))
