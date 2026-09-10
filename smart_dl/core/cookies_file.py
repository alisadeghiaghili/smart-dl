"""Netscape cookies.txt load/save for yt-dlp and requests."""

from __future__ import annotations

from http.cookiejar import MozillaCookieJar
from pathlib import Path
from typing import Optional, Tuple

__all__ = [
    "count_cookies_for_domain",
    "get_cookies_file",
    "load_netscape_cookies",
    "save_cookies_file",
    "set_cookies_file",
]


def get_cookies_file() -> str:
    """Return the saved cookies.txt path from config (may be empty)."""
    from smart_dl.core.config import load_config

    return str(load_config().get("cookies_file") or "")


def set_cookies_file(path: str) -> bool:
    """Persist a cookies.txt path in config.

    Parameters
    ----------
    path : str
        Absolute or relative path to a Netscape cookies file.

    Returns
    -------
    bool
        ``True`` if config save succeeded.
    """
    from smart_dl.core.config import load_config, save_config

    cfg = load_config()
    cfg["cookies_file"] = str(path)
    return save_config(cfg)


def save_cookies_file(path: str = "") -> bool:
    """Clear or set the cookies file path (empty clears)."""
    if not path:
        return set_cookies_file("")
    return set_cookies_file(path)


def load_netscape_cookies(path: Optional[str] = None) -> Tuple[bool, str]:
    """Load a Netscape-format cookies.txt file.

    Parameters
    ----------
    path : str, optional
        File path; uses config ``cookies_file`` when omitted.

    Returns
    -------
    (bool, str)
        Success flag and a short message (path or error).
    """
    file_path = path or get_cookies_file()
    if not file_path:
        return False, "no cookies file configured (--cookies-file)"
    p = Path(file_path)
    if not p.is_file():
        return False, f"not found: {file_path}"
    jar = MozillaCookieJar(str(p))
    try:
        jar.load(ignore_discard=True, ignore_expires=True)
    except Exception as exc:  # noqa: BLE001
        return False, f"parse error: {exc}"
    return True, f"{len(jar)} cookies from {file_path}"


def count_cookies_for_domain(
    path: Optional[str] = None, domain: str = "youtube.com"
) -> int:
    """Count cookies for *domain* in a Netscape file.

    Parameters
    ----------
    path : str, optional
        Cookies file path.
    domain : str, optional
        Domain suffix to match.

    Returns
    -------
    int
        Number of matching cookies (0 on error).
    """
    file_path = path or get_cookies_file()
    if not file_path or not Path(file_path).is_file():
        return 0
    jar = MozillaCookieJar(str(file_path))
    try:
        jar.load(ignore_discard=True, ignore_expires=True)
    except Exception:
        return 0
    domain = domain.lower().lstrip(".")
    count = 0
    for cookie in jar:
        d = (cookie.domain or "").lower().lstrip(".")
        if d == domain or d.endswith("." + domain):
            count += 1
    return count


def netscape_cookiejar(path: Optional[str] = None) -> Optional[MozillaCookieJar]:
    """Return a loaded MozillaCookieJar or None."""
    file_path = path or get_cookies_file()
    if not file_path or not Path(file_path).is_file():
        return None
    jar = MozillaCookieJar(str(file_path))
    try:
        jar.load(ignore_discard=True, ignore_expires=True)
        return jar
    except Exception:
        return None
