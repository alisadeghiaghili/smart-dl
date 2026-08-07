"""Proxy detection, menu, apply/clear."""
import os
import re
from urllib.parse import urlparse

from rich import box
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from smart_dl.core.config import load_config, save_config
from smart_dl.ui import console, info, success, warn

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

_PROXY_ENV_VARS = (
    "HTTPS_PROXY", "https_proxy",
    "HTTP_PROXY",  "http_proxy",
    "ALL_PROXY",   "all_proxy",
    "SOCKS5_PROXY", "socks5_proxy",
    "SOCKS_PROXY",  "socks_proxy",
    "SOCKS4_PROXY", "socks4_proxy",
)

_SOCKS5_HINT_PORTS = {10808, 1080, 9050, 9150}


def _is_socks_port(addr: str) -> bool:
    m = re.search(r':(\d+)$', addr)
    if not m:
        return False
    try:
        return int(m.group(1)) in _SOCKS5_HINT_PORTS
    except ValueError:
        return False


def _peek_env_proxy() -> str:
    """Read proxy from environment variables only. No side effects."""
    for var in _PROXY_ENV_VARS:
        v = os.environ.get(var, "").strip()
        if v:
            return v
    return ""


def _peek_registry_proxy() -> str:
    """Read proxy from Windows registry. Returns "" if unavailable or invalid.

    Handles the three shapes Windows uses:
      - host:port
      - http=host:port;https=host:port
      - socks=host:port;http=host:port;https=host:port (v2rayN/Hiddify/Nekoray)
    Prefers SOCKS when present (Iranian proxy clients), falls back to https/http.
    """
    try:
        import winreg as _wr
    except ImportError:
        return ""

    try:
        key = _wr.OpenKey(_wr.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
        enabled, _ = _wr.QueryValueEx(key, "ProxyEnable")
        if not enabled:
            return ""
        server, _ = _wr.QueryValueEx(key, "ProxyServer")
    except (OSError, FileNotFoundError):
        return ""

    if not server:
        return ""

    if "=" not in server:
        if _is_socks_port(server):
            return f"socks5://{server}"
        return f"http://{server}"

    parts: dict[str, str] = {}
    for segment in server.split(";"):
        if "=" in segment:
            k, v = segment.split("=", 1)
            parts[k.strip().lower()] = v.strip()

    socks = parts.get("socks") or parts.get("socks5")
    if socks:
        return f"socks5://{socks}"

    https_p = parts.get("https")
    if https_p:
        return f"http://{https_p}"

    http_p = parts.get("http")
    if http_p:
        return f"http://{http_p}"

    return ""


def peek_current_proxy() -> str:
    """Read the currently active proxy from env / config / registry. Read-only.

    Order: env vars → saved config → Windows registry. Does NOT mutate config
    or env vars. Returns "" if no proxy is set anywhere.
    """
    env = _peek_env_proxy()
    if env:
        return env

    cfg_proxy = load_config().get("proxy", "").strip()
    if cfg_proxy:
        return cfg_proxy

    reg = _peek_registry_proxy()
    return reg


def get_current_proxy() -> str:
    """Backwards-compatible read of the current proxy.

    Same as peek_current_proxy() — kept as an alias for existing callers.
    """
    return peek_current_proxy()


def _looks_like_proxy_url(addr: str) -> bool:
    """Return True if addr parses as a URL with host + port."""
    if not addr:
        return False
    try:
        parsed = urlparse(addr)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https", "socks4", "socks5", "socks"):
        return False
    if not parsed.hostname:
        return False
    if parsed.port is None:
        return False
    return True


def apply_proxy(addr: str) -> bool:
    """Set proxy in env vars and persist to config.

    Returns True on success, False if `addr` does not look like a valid proxy URL.
    Rejects malformed input so a bad registry parse can't poison config.json.
    """
    addr = (addr or "").strip()
    if not addr:
        return False
    if not _looks_like_proxy_url(addr):
        warn("Not a valid proxy URL: " + addr)
        return False
    os.environ["HTTP_PROXY"]  = addr
    os.environ["HTTPS_PROXY"] = addr
    cfg = load_config()
    cfg["proxy"] = addr
    save_config(cfg)
    return True


def clear_proxy():
    """Remove proxy from env vars and config."""
    for k in _PROXY_ENV_VARS:
        os.environ.pop(k, None)
    cfg = load_config()
    cfg["proxy"] = ""
    save_config(cfg)


def hint_proxy_port(addr):
    """Warn if port suggests wrong protocol (e.g. SOCKS5 port with HTTP)."""
    if not addr:
        return
    m = re.search(r':(\d+)$', addr)
    if not m:
        return
    try:
        port = int(m.group(1))
    except ValueError:
        return
    if port in _SOCKS5_HINT_PORTS:
        warn("Port " + str(port) + " is typically used for SOCKS5, not HTTP.")
        info("If the connection fails, try: socks5://" + addr.split("://", 1)[-1])


def proxy_menu():
    """Interactive proxy configuration menu."""
    while True:
        console.print()
        t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
        t.add_column(style="bold cyan", width=4, justify="right")
        t.add_column(style="white")
        t.add_column(style="dim")
        t.add_row("1", "Enter proxy address manually", "(http://host:port or socks5://host:port)")
        t.add_row("2", "Use localhost port", "(v2rayN \u00b7 Clash \u00b7 Hiddify \u00b7 Nekoray)")
        t.add_row("3", "I'm using a VPN", "(WireGuard \u00b7 OpenVPN \u00b7 AnyConnect)")
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
                apply_proxy(addr)
                hint_proxy_port(addr)
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
                    apply_proxy(addr); hint_proxy_port(addr); success("Proxy set: " + addr)
            elif sel.isdigit() and 1 <= int(sel) <= len(LOCALHOST_PORTS):
                port, _ = LOCALHOST_PORTS[int(sel)-1]
                addr = "http://127.0.0.1:" + str(port)
                apply_proxy(addr); hint_proxy_port(addr); success("Proxy set: " + addr)
            break
        elif ch == "3":
            clear_proxy()
            console.print(Panel(
                "[bold green]  Proxy cleared.[/bold green]\n\n"
                "  [dim]WireGuard, OpenVPN, and AnyConnect route traffic at the system\n"
                "  level \u2014 no local proxy needed. SmartDL will use your VPN directly.\n\n"
                "  If downloads were failing with a proxy set, this should fix it.[/dim]",
                border_style="green", title="[bold green]  VPN Mode[/bold green]", padding=(0, 2)
            ))
            break
        elif ch == "4":
            clear_proxy(); success("Proxy cleared.")
            break
        else:
            warn("Invalid selection.")


def proxy_step():
    """Prompt user to configure proxy at startup."""
    current = get_current_proxy()
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
            proxy_menu()
    else:
        console.print()
        console.print(Panel("[dim]No proxy configured.[/dim]\n  Press [bold cyan]P[/bold cyan] to set a proxy   or   [bold]Enter[/bold] to skip", border_style="dim", title="[dim]Proxy[/dim]", padding=(0,2)))
        while True:
            ch = Prompt.ask("  [bold yellow]> (Enter / p)[/bold yellow]", default="").strip().lower()
            if ch in ("", "p"):
                break
            warn("Invalid input \u2014 press Enter to skip or P to set proxy.")
        if ch == "p":
            proxy_menu()
