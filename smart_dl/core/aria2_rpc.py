"""aria2 JSON-RPC client (roadmap R11) — optional when aria2 RPC is running."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Sequence
from urllib.request import Request, urlopen

__all__ = [
    "aria2_rpc_enabled",
    "get_aria2_rpc_settings",
    "send_to_aria2_rpc",
]

HttpPost = Callable[..., Any]


def get_aria2_rpc_settings(config: Optional[dict] = None) -> Dict[str, str]:
    """Read aria2 RPC settings from config.

    Parameters
    ----------
    config : dict, optional
        Config mapping; loaded when omitted.

    Returns
    -------
    dict
        Keys ``url`` and ``secret`` (either may be empty).
    """
    from smart_dl.core.config import load_config

    cfg = config if config is not None else load_config()
    url = str(cfg.get("aria2_rpc_url") or "").strip()
    secret = str(cfg.get("aria2_rpc_secret") or "").strip()
    # Allow bare host:port
    if url and not url.startswith("http"):
        url = "http://" + url
    if url and not url.endswith("/jsonrpc"):
        url = url.rstrip("/") + "/jsonrpc"
    return {"url": url, "secret": secret}


def aria2_rpc_enabled(config: Optional[dict] = None) -> bool:
    """Return True when an aria2 RPC URL is configured.

    Parameters
    ----------
    config : dict, optional
        Config mapping.

    Returns
    -------
    bool
    """
    return bool(get_aria2_rpc_settings(config)["url"])


def _rpc_payload(
    method: str,
    params: Sequence[Any],
    secret: str,
    req_id: int = 1,
) -> Dict[str, Any]:
    rpc_params: List[Any] = []
    if secret:
        rpc_params.append(f"token:{secret}")
    rpc_params.extend(params)
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": rpc_params}


def send_to_aria2_rpc(
    urls: Sequence[str],
    *,
    config: Optional[dict] = None,
    http: Optional[HttpPost] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Queue URLs into aria2 via JSON-RPC ``aria2.addUri``.

    Parameters
    ----------
    urls : sequence of str
        Download URIs.
    config : dict, optional
        Config with ``aria2_rpc_url`` / optional ``aria2_rpc_secret``.
    http : Callable, optional
        Injectable poster ``(url, data=bytes, timeout=float) -> response``.
    timeout : float, optional
        Request timeout.

    Returns
    -------
    dict
        ``ok`` (bool), ``results`` (list), ``error`` (str|None), ``url`` (str).

    Examples
    --------
    >>> send_to_aria2_rpc(["https://x"], config={"aria2_rpc_url": ""})["ok"]
    False
    """
    settings = get_aria2_rpc_settings(config)
    rpc_url = settings["url"]
    if not rpc_url:
        return {"ok": False, "results": [], "error": "aria2_rpc_url not set", "url": ""}

    results: List[Any] = []
    try:
        for index, item in enumerate(urls, start=1):
            payload = _rpc_payload("aria2.addUri", [[item]], settings["secret"], req_id=index)
            body = json.dumps(payload).encode("utf-8")
            if http is not None:
                resp = http(rpc_url, data=body, timeout=timeout)
                raw = getattr(resp, "read", lambda: b"{}")()
            else:
                request = Request(
                    rpc_url,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=timeout) as response:  # noqa: S310 — localhost RPC
                    raw = response.read()
            data = json.loads(raw.decode("utf-8") or "{}")
            if isinstance(data, dict) and data.get("error"):
                return {
                    "ok": False,
                    "results": results,
                    "error": str(data["error"]),
                    "url": rpc_url,
                }
            results.append(data.get("result") if isinstance(data, dict) else data)
        return {"ok": True, "results": results, "error": None, "url": rpc_url}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "results": results, "error": f"{type(exc).__name__}: {exc}", "url": rpc_url}
