"""Faradars Next.js helpers (buildId + page JSON)."""

from __future__ import annotations

import re
from typing import Optional

__all__ = ["extract_next_build_id", "fetch_faradars_page_json", "title_from_next_json"]


def extract_next_build_id(html: str) -> str:
    """Extract Next.js ``buildId`` from page HTML.

    Parameters
    ----------
    html : str
        Page HTML.

    Returns
    -------
    str
        Build id, or empty string.
    """
    match = re.search(r'"buildId"\s*:\s*"([^"]+)"', html or "")
    return match.group(1) if match else ""


def fetch_faradars_page_json(url: str, html: str = "") -> Optional[dict]:
    """Fetch ``/_next/data/{buildId}/fa/{path}.json`` for a Faradars page.

    Parameters
    ----------
    url : str
        Page URL (e.g. ``https://faradars.org/how-to-learn/python``).
    html : str, optional
        Already-fetched HTML used to read ``buildId``.

    Returns
    -------
    dict or None
        Parsed Next.js page JSON.
    """
    from urllib.parse import urlparse

    import requests

    from smart_dl.core.proxy import get_current_proxy

    parsed = urlparse(url)
    if parsed.netloc and "faradars.org" not in parsed.netloc:
        return None
    path = parsed.path.strip("/")
    if not path:
        return None

    if not html:
        from smart_dl.extractors.education import _fetch_html

        html = _fetch_html(url)
    build_id = extract_next_build_id(html)
    if not build_id:
        return None

    json_url = f"https://faradars.org/_next/data/{build_id}/fa/{path}.json"
    proxy = get_current_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        resp = requests.get(
            json_url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            proxies=proxies,
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def title_from_next_json(data: Optional[dict]) -> str:
    """Pull a human title from Faradars Next.js page JSON.

    Parameters
    ----------
    data : dict or None
        Output of :func:`fetch_faradars_page_json`.

    Returns
    -------
    str
        Title if found.
    """
    if not data:
        return ""
    props = data.get("pageProps") or {}
    for key in ("title", "courseTitle", "name"):
        value = props.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    # appFallback is a dict keyed by request JSON
    fallback = props.get("appFallback")
    if isinstance(fallback, dict):
        for node in fallback.values():
            if not isinstance(node, dict):
                continue
            page = node.get("data") or {}
            if isinstance(page, dict):
                for key in ("title", "name"):
                    value = page.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
    return ""
