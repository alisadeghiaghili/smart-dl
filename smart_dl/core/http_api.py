"""Local HTTP control API (roadmap R10).

Binds **localhost only**. Optional bearer token from config key ``api_token``.
Stdlib-only (no FastAPI dependency).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

__all__ = [
    "DEFAULT_API_HOST",
    "DEFAULT_API_PORT",
    "api_token_ok",
    "build_handler",
    "handle_api_request",
    "start_api_server",
]

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8765

# Extra safety: never bind non-loopback from this module.
_ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}


def api_token_ok(
    provided: Optional[str],
    *,
    config: Optional[dict] = None,
) -> bool:
    """Validate bearer token against config when a token is required.

    If no ``api_token`` is configured, the API allows local requests
    (documented trade-off for personal desktop use).

    Parameters
    ----------
    provided : str or None
        Token from Authorization header / query.
    config : dict, optional
        Config mapping.

    Returns
    -------
    bool
    """
    from smart_dl.core.config import load_config

    cfg = config if config is not None else load_config()
    expected = str(cfg.get("api_token") or "").strip()
    if not expected:
        return True
    return (provided or "").strip() == expected


def _extract_token(handler_headers: Dict[str, str], query: Dict[str, list]) -> str:
    auth = handler_headers.get("Authorization") or handler_headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    q = query.get("token") or query.get("api_token") or []
    return str(q[0]) if q else ""


def handle_api_request(
    method: str,
    path: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    body: bytes = b"",
    config: Optional[dict] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Dispatch one API request (pure function for tests).

    Routes
    ------
    GET  /health
    GET  /queue
    GET  /history?limit=20
    POST /queue          body: ``{"urls": ["https://..."]}``

    Parameters
    ----------
    method : str
        HTTP method.
    path : str
        URL path (query string allowed).
    headers : dict, optional
        Request headers.
    body : bytes, optional
        Raw body.
    config : dict, optional
        Config for token check.

    Returns
    -------
    (int, dict)
        Status code and JSON payload.
    """
    parsed = urlparse(path)
    route = (parsed.path or "/").rstrip("/") or "/"
    query = parse_qs(parsed.query or "")
    token = _extract_token(headers or {}, query)

    if not api_token_ok(token, config=config):
        return 401, {"ok": False, "error": "unauthorized"}

    method = method.upper()

    if route == "/health" and method == "GET":
        from smart_dl import VERSION

        return 200, {"ok": True, "app": "smart-dl", "version": VERSION}

    if route == "/queue" and method == "GET":
        from smart_dl.core.queue import get_queue, get_queue_stats, init_db

        init_db()
        return 200, {"ok": True, "stats": get_queue_stats(), "items": get_queue()}

    if route == "/queue" and method == "POST":
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return 400, {"ok": False, "error": "invalid JSON"}
        urls = data.get("urls") if isinstance(data, dict) else None
        if not isinstance(urls, list) or not urls:
            return 400, {"ok": False, "error": "urls array required"}
        from smart_dl.core.queue import add_to_queue, init_db

        init_db()
        added = add_to_queue([str(u) for u in urls])
        return 200, {"ok": True, "added": added}

    if route == "/history" and method == "GET":
        from smart_dl.core.history import get_history, init_db

        init_db()
        limit = 20
        try:
            limit = int((query.get("limit") or ["20"])[0])
        except ValueError:
            limit = 20
        rows = get_history(limit=max(1, min(limit, 200)))
        return 200, {"ok": True, "items": rows}

    return 404, {"ok": False, "error": "not found"}


def build_handler(config: Optional[dict] = None) -> type:
    """Build a BaseHTTPRequestHandler bound to :func:`handle_api_request`.

    Parameters
    ----------
    config : dict, optional
        Config snapshot for token validation.

    Returns
    -------
    type
        Handler class.
    """

    class _ApiHandler(BaseHTTPRequestHandler):
        server_version = "SmartDLAPI/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
            return  # keep CLI clean

        def _send(self, status: int, payload: Dict[str, Any]) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            status, payload = handle_api_request(
                "GET", self.path, headers=dict(self.headers), config=config
            )
            self._send(status, payload)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
            status, payload = handle_api_request(
                "POST",
                self.path,
                headers=dict(self.headers),
                body=body,
                config=config,
            )
            self._send(status, payload)

    return _ApiHandler


def start_api_server(
    *,
    host: str = DEFAULT_API_HOST,
    port: int = DEFAULT_API_PORT,
    config: Optional[dict] = None,
    background: bool = True,
) -> ThreadingHTTPServer:
    """Start the local control API.

    Parameters
    ----------
    host : str, optional
        Must be a loopback host.
    port : int, optional
        TCP port.
    config : dict, optional
        Config for token checks.
    background : bool, optional
        When True, serve in a daemon thread (tests/CLI).

    Returns
    -------
    ThreadingHTTPServer
        Running server instance.

    Raises
    ------
    ValueError
        If host is not loopback.
    """
    if host not in _ALLOWED_HOSTS:
        raise ValueError("API server may only bind to localhost")

    handler = build_handler(config=config)
    server = ThreadingHTTPServer((host, port), handler)
    if background:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
    return server
