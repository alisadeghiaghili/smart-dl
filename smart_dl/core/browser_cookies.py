"""Browser cookie helpers for requests sessions."""

from __future__ import annotations

import logging
from typing import Optional

import requests

from smart_dl.core.cookies import get_cookie_browser

__all__ = ["build_session", "session_with_browser_cookies"]

_logger = logging.getLogger(__name__)


def session_with_browser_cookies(
    browser: Optional[str] = None,
    *,
    domains: Optional[list] = None,
) -> requests.Session:
    """Create a requests session and load cookies from a local browser.

    Parameters
    ----------
    browser : str, optional
        Browser name (``firefox``, ``chrome``, ``edge``, ...). Defaults to
        the saved SmartDL cookie browser.
    domains : list of str, optional
        Cookie domain filters (e.g. ``["coursera.org"]``). When omitted all
        browser cookies are loaded.

    Returns
    -------
    requests.Session
        Session with cookies applied when extraction succeeds. On failure
        the session is returned empty (caller can still try anonymously).

    Examples
    --------
    >>> session = session_with_browser_cookies("firefox", domains=["coursera.org"])
    >>> # session.get(...)  # doctest: +SKIP
    """
    session = requests.Session()
    browser = browser or get_cookie_browser()
    if not browser:
        return session

    try:
        from yt_dlp.cookies import extract_cookies_from_browser
    except ImportError:
        return session

    try:
        jar = extract_cookies_from_browser(browser)
    except Exception as exc:  # noqa: BLE001 — browser lock / missing / encrypted
        _logger.debug("cookie extract failed for %s: %s", browser, exc)
        return session

    if jar is None:
        return session

    allowed = {d.lower().lstrip(".") for d in (domains or [])}
    for cookie in jar:
        domain = (cookie.domain or "").lower().lstrip(".")
        if allowed and not any(domain == d or domain.endswith("." + d) for d in allowed):
            continue
        try:
            session.cookies.set_cookie(cookie)
        except Exception:
            continue
    return session


def build_session(proxy: Optional[str] = None) -> requests.Session:
    """Create a session with optional proxy (no browser cookies).

    Parameters
    ----------
    proxy : str, optional
        Proxy URL.

    Returns
    -------
    requests.Session
        Configured session.
    """
    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session
