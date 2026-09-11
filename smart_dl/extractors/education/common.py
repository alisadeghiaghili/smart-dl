"""Common types, patterns, and helpers for education platforms."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List
from urllib.parse import urljoin, urlparse

from smart_dl.core.net_utils import host_matches, url_host

_MAKTAB_HOSTS = ("maktabkhooneh.org", "www.maktabkhooneh.org")
_FARADARS_HOSTS = ("faradars.org", "www.faradars.org")
_COURSERA_HOSTS = ("coursera.org", "www.coursera.org")

_LESSON_HREF_RE = re.compile(
    r"""href=["'](
        [^"']*?/ویدیو-[^"']*
        |
        [^"']*?/video-[^"']*
        |
        [^"']*?/lesson/[^"']*
        |
        [^"']*?/fv[0-9]+[^"']*
        |
        [^"']*?/learn/[^"']*/lecture/[^"']*
        |
        [^"']*?/lecture/[^"']*
    )["']""",
    re.IGNORECASE | re.VERBOSE,
)

_NUXT_SLUG_RE = re.compile(r'["\'](ویدیو-[^"\']{2,120})["\']')
_MEDIA_URL_RE = re.compile(
    r'https?://[^"\'\s\\]+?(?:\.mp4|\.m3u8)[^"\'\s\\]*',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CourseLesson:
    """One downloadable lesson inside a course."""

    title: str
    url: str
    index: int = 0

    def as_dict(self) -> dict:
        return {"title": self.title, "url": self.url, "index": self.index}


@dataclass
class CourseOutline:
    """Parsed course page metadata."""

    platform: str
    course_url: str
    title: str = ""
    lessons: List[CourseLesson] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.lessons)


def is_maktabkhooneh_url(url: str) -> bool:
    """Check whether *url* is a Maktabkhooneh link."""
    return host_matches(url_host(url), _MAKTAB_HOSTS)


def is_faradars_url(url: str) -> bool:
    """Check whether *url* is a Faradars link."""
    return host_matches(url_host(url), _FARADARS_HOSTS)


def is_coursera_url(url: str) -> bool:
    """Check whether *url* is a Coursera link."""
    return host_matches(url_host(url), _COURSERA_HOSTS)


def is_education_url(url: str) -> bool:
    """Check whether *url* belongs to any supported education platform."""
    return is_maktabkhooneh_url(url) or is_faradars_url(url) or is_coursera_url(url)


def platform_name(url: str) -> str:
    """Human-readable platform name for UI and messages."""
    if is_maktabkhooneh_url(url):
        return "Maktabkhooneh"
    if is_faradars_url(url):
        return "Faradars"
    if is_coursera_url(url):
        return "Coursera"
    return "Unknown"


def extract_nuxt_lesson_slugs(html: str) -> List[str]:
    """Extract Maktabkhooneh lesson slugs from an SSR/Nuxt payload."""
    found: List[str] = []
    for match in _NUXT_SLUG_RE.finditer(html or ""):
        slug = match.group(1).strip()
        if slug not in found:
            found.append(slug)
    return found


def extract_media_urls(html: str) -> List[str]:
    """Extract direct media file URLs (mp4/m3u8) from page HTML."""
    found: List[str] = []
    for match in _MEDIA_URL_RE.finditer(html or ""):
        url = match.group(0).replace("\\u0026", "&").replace("\\/", "/")
        if url not in found:
            found.append(url)
    return found


def extract_lesson_hrefs(html: str, base_url: str) -> List[str]:
    """Extract unique lesson/video hrefs from a course HTML page."""
    html = html or ""
    seen: List[str] = []
    for match in _LESSON_HREF_RE.finditer(html):
        href = match.group(1).strip()
        absolute = urljoin(base_url, href)
        if absolute not in seen:
            seen.append(absolute)

    if seen:
        return seen

    mk = is_maktabkhooneh_url(base_url)
    course_path = urlparse(base_url).path.rstrip("/")
    if not mk or not course_path.startswith("/course/"):
        return seen

    slugs = extract_nuxt_lesson_slugs(html)
    for slug in slugs:
        absolute = urljoin(base_url, course_path + "/" + slug)
        if absolute not in seen:
            seen.append(absolute)
    return seen


def fetch_html(url: str) -> str:
    """Fetch page HTML using browser cookies and proxy when available."""
    from urllib.parse import urlparse

    from smart_dl.core.cookies import get_cookie_browser
    from smart_dl.core.proxy import get_current_proxy

    proxy = get_current_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
    }

    browser = get_cookie_browser()
    if browser:
        from smart_dl.core.browser_cookies import session_with_browser_cookies

        domain = urlparse(url).hostname or ""
        session = session_with_browser_cookies(
            browser, domains=[domain] if domain else None,
        )
    else:
        import requests

        session = requests.Session()

    if proxies:
        session.proxies.update(proxies)

    try:
        resp = session.get(
            url, timeout=20, headers=headers, allow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text or ""
    except Exception:
        return ""
