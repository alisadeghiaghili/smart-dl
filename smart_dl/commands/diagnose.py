"""CLI diagnostics panel."""

from __future__ import annotations

from typing import List

__all__ = ["print_diagnostics", "tool_version"]


def tool_version(tool: str) -> str:
    """Return the version string of *tool* if it is on PATH.

    Parameters
    ----------
    tool : str
        Executable name.

    Returns
    -------
    str
        Version line, or ``"not found"``.
    """
    import shutil
    import subprocess

    path = shutil.which(tool)
    if not path:
        return "not found"
    try:
        proc = subprocess.run(
            [tool, "--version"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        first = (proc.stdout or proc.stderr or "").splitlines()
        return first[0][:80] if first else "unknown"
    except Exception as exc:  # noqa: BLE001 — diagnostics must not crash
        return f"error: {type(exc).__name__}"


def print_diagnostics() -> None:
    """Print environment diagnostics for ``--diagnose``.

    Returns
    -------
    None
    """
    import os
    import platform
    import sys

    from rich.console import Console
    from rich.panel import Panel

    from smart_dl import VERSION
    from smart_dl.core.paths import get_data_dir, is_portable
    from smart_dl.core.proxy import _PROXY_ENV_VARS, peek_current_proxy

    lines: List[str] = [
        f"    SmartDL v{VERSION}  —  diagnostics",
        "",
        f"    Python      : {platform.python_version()}",
        f"    Python exe  : {sys.executable}",
        f"    Platform    : {platform.platform()}",
        "",
        "    --- External tools ---",
        f"    ffmpeg      : {tool_version('ffmpeg')}",
        f"    node        : {tool_version('node')}",
        f"    aria2c      : {tool_version('aria2c')}",
        f"    winget      : {tool_version('winget')}",
        "",
        "    --- Proxy state ---",
        f"    Active      : {peek_current_proxy() or 'none'}",
    ]

    env_proxies = [(k, os.environ.get(k)) for k in _PROXY_ENV_VARS if os.environ.get(k)]
    if env_proxies:
        lines.append("  Env vars    :")
        for key, val in env_proxies:
            lines.append(f"    {key} = {val}")
    else:
        lines.append("  Env vars    : [dim]none[/dim]")
    lines.append("")
    lines.append("  --- Browser cookies ---")
    from smart_dl.core.cookie_diag import cookie_diagnose_report
    from smart_dl.core.cookies_file import get_cookies_file

    cookie_report = cookie_diagnose_report()
    if not cookie_report["configured"]:
        lines.append("  Browser     : [dim]not set[/dim] (press c at the URL prompt)")
    else:
        lines.append(f"  Browser     : {cookie_report['browser']}")
        if cookie_report["extract_ok"]:
            lines.append(f"  Cookies     : {cookie_report['total_cookies']} total")
            by_domain = cookie_report.get("by_domain") or {}
            if isinstance(by_domain, dict):
                for domain, count in by_domain.items():
                    mark = "[green]ok[/green]" if count else "[dim]0[/dim]"
                    lines.append(f"    {domain:20s} {count}  {mark}")
        else:
            lines.append(f"  Extract     : [red]FAILED[/red] {cookie_report['error']}")
    cookie_path = get_cookies_file()
    lines.append(f"  cookies.txt : {cookie_path or '[dim]not set[/dim]'}")
    lines.append("")
    lines.append("  --- Paths ---")
    lines.append(f"  Portable    : {is_portable()}")
    lines.append(f"  Data dir    : {get_data_dir()}")
    lines.append(f"  Config      : {get_data_dir() / 'config.json'}")
    lines.append("")
    lines.append("  --- Network test ---")
    try:
        import requests

        response = requests.head("https://www.youtube.com", timeout=5, allow_redirects=True)
        lines.append(f"  youtube.com : HTTP {response.status_code} (OK)")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"  youtube.com : FAILED ({type(exc).__name__}: {str(exc)[:80]})")

    console = Console()
    console.print()
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold cyan]SmartDL Diagnostics[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
