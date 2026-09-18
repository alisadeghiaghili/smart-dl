"""CLI handlers for Wave 4: aria2 RPC (R11) and local HTTP API (R10)."""

from __future__ import annotations

from typing import Optional, Sequence

__all__ = ["handle_aria2_rpc", "handle_api_server"]


def handle_aria2_rpc(urls: Optional[Sequence[str]]) -> None:
    """Send URLs to a configured aria2 JSON-RPC endpoint.

    Parameters
    ----------
    urls : sequence of str or None
        URIs to queue in aria2.

    Returns
    -------
    None
    """
    from smart_dl.core.aria2_rpc import aria2_rpc_enabled, send_to_aria2_rpc
    from smart_dl.lang import t
    from smart_dl.ui import error, info, success

    if not aria2_rpc_enabled():
        error(t("cli_aria2_not_configured"))
        info("Set with: config key aria2_rpc_url (e.g. http://127.0.0.1:6800/jsonrpc)")
        return
    targets = [u for u in (urls or []) if u]
    if not targets:
        error("Usage: --aria2-rpc URL [URL...]")
        return
    result = send_to_aria2_rpc(targets)
    if result.get("ok"):
        success(t("cli_aria2_ok", n=len(targets)))
        info(f"RPC: {result.get('url')}")
    else:
        error(f"aria2 RPC failed: {result.get('error')}")


def handle_api_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    foreground: bool = True,
) -> None:
    """Start the local control API on localhost.

    Parameters
    ----------
    host : str, optional
        Loopback host only.
    port : int, optional
        TCP port.
    foreground : bool, optional
        Block until Ctrl+C when True.

    Returns
    -------
    None
    """
    from smart_dl.core.http_api import start_api_server
    from smart_dl.lang import t
    from smart_dl.ui import info, success, warn
    from smart_dl.ui.progress import stop_event

    try:
        server = start_api_server(host=host, port=port, background=True)
    except (OSError, ValueError) as exc:
        warn(f"API start failed: {exc}")
        return
    success(t("cli_api_listening", host=host, port=port))
    info("GET /health | GET /queue | POST /queue {\"urls\":[...]} | GET /history")
    info("Optional auth: config api_token → Authorization: Bearer <token>")
    if not foreground:
        return
    try:
        while not stop_event.is_set():
            stop_event.wait(0.5)
    except KeyboardInterrupt:
        info("API server stopping.")
    finally:
        server.shutdown()
