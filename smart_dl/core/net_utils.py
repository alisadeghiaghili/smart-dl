"""Host and URL classification helpers."""

from __future__ import annotations

from typing import Iterable, Optional
from urllib.parse import urlparse

__all__ = [
    "host_matches",
    "normalize_host",
    "url_host",
]


def normalize_host(host: str) -> str:
    """Lowercase a host and strip a leading ``www.`` and port.

    Parameters
    ----------
    host : str
        Hostname or ``host:port``.

    Returns
    -------
    str
        Normalized hostname (may be empty).
    """
    host = (host or "").strip().lower()
    if not host:
        return ""
    # Strip credentials if present (user:pass@host)
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def url_host(url: str) -> str:
    """Extract the normalized hostname from a URL.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    str
        Normalized host, or ``""`` if parsing fails.
    """
    try:
        return normalize_host(urlparse(url).netloc)
    except ValueError:
        return ""


def host_matches(host: str, candidates: Iterable[str]) -> bool:
    """Return whether *host* equals or is a subdomain of any candidate.

    Unlike a substring check, ``evil-youtube.com.attacker.net`` does not
    match ``youtube.com``.

    Parameters
    ----------
    host : str
        Hostname (already extracted, or raw).
    candidates : Iterable[str]
        Candidate domains such as ``("youtube.com", "youtu.be")``.

    Returns
    -------
    bool
        ``True`` on exact or subdomain match.
    """
    normalized = normalize_host(host)
    if not normalized:
        return False
    for candidate in candidates:
        candidate_n = normalize_host(candidate)
        if not candidate_n:
            continue
        if normalized == candidate_n or normalized.endswith("." + candidate_n):
            return True
    return False


def is_http_url(url: str) -> bool:
    """Check whether *url* is an http(s) or ftp URL.

    Parameters
    ----------
    url : str
        Candidate URL.

    Returns
    -------
    bool
        ``True`` if scheme is ``http``, ``https``, or ``ftp``.
    """
    try:
        scheme = urlparse(url or "").scheme.lower()
    except ValueError:
        return False
    return scheme in ("http", "https", "ftp")


def platform_from_url(url: str, mapping: dict) -> Optional[str]:
    """Look up a platform label by URL host using *mapping*.

    Parameters
    ----------
    url : str
        Absolute URL.
    mapping : dict
        Domain → label map. Keys may include ``www.`` variants.

    Returns
    -------
    str or None
        Label if the host matches a key, else ``None``.
    """
    host = url_host(url)
    if not host:
        return None
    for domain, label in mapping.items():
        if host_matches(host, (domain,)):
            return label
    return None
