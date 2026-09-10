"""Cookie-browser diagnostic summary for --diagnose."""

from __future__ import annotations

from typing import Dict, List, Optional

__all__ = ["cookie_diagnose_report"]


def cookie_diagnose_report(
    domains: Optional[List[str]] = None,
    *,
    browser: Optional[str] = None,
) -> Dict[str, object]:
    """Summarize the configured cookie browser and cookie counts.

    Parameters
    ----------
    domains : list of str, optional
        Domains to count (default YouTube / Coursera / Maktabkhooneh).
    browser : str, optional
        Override saved browser name.

    Returns
    -------
    dict
        Keys: ``configured``, ``browser``, ``extract_ok``, ``error``,
        ``total_cookies``, ``by_domain``.
    """
    from smart_dl.core.cookies import get_cookie_browser

    report: Dict[str, object] = {
        "configured": False,
        "browser": "",
        "extract_ok": False,
        "error": "",
        "total_cookies": 0,
        "by_domain": {},
    }
    name = browser or get_cookie_browser()
    report["browser"] = name or ""
    report["configured"] = bool(name)
    if not name:
        report["error"] = "no cookie browser set (press c at the URL prompt)"
        return report

    try:
        from yt_dlp.cookies import extract_cookies_from_browser
    except ImportError:
        report["error"] = "yt-dlp cookies module unavailable"
        return report

    try:
        jar = extract_cookies_from_browser(name)
    except Exception as exc:  # noqa: BLE001
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report

    if jar is None:
        report["error"] = "empty cookie jar"
        return report

    targets = domains or [
        "youtube.com",
        "maktabkhooneh.org",
        "faradars.org",
        "coursera.org",
        "aparat.com",
    ]
    counts = {d: 0 for d in targets}
    total = 0
    for cookie in jar:
        total += 1
        domain = (cookie.domain or "").lower().lstrip(".")
        for target in targets:
            if domain == target or domain.endswith("." + target):
                counts[target] += 1
                break
    report["extract_ok"] = True
    report["total_cookies"] = total
    report["by_domain"] = counts
    return report
