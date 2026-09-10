"""Education platform extractors — Maktabkhooneh and Faradars.

Paid course content requires a logged-in browser session. SmartDL reuses
the existing cookie-browser setting so yt-dlp can fetch authorized streams.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlparse

from smart_dl.core.net_utils import host_matches, url_host
from smart_dl.ui import error, info, print_section, success, warn

__all__ = [
    "CourseLesson",
    "CourseOutline",
    "download_education_course",
    "extract_lesson_hrefs",
    "is_education_url",
    "is_faradars_url",
    "is_maktabkhooneh_url",
    "platform_name",
]

_MAKTAB_HOSTS = ("maktabkhooneh.org", "www.maktabkhooneh.org")
_FARADARS_HOSTS = ("faradars.org", "www.faradars.org")

# Lesson / video path fragments used by both platforms.
_LESSON_HREF_RE = re.compile(
    r"""href=["'](
        [^"']*?/ویدیو-[^"']*
        |
        [^"']*?/video-[^"']*
        |
        [^"']*?/lesson/[^"']*
        |
        [^"']*?/fv[0-9]+[^"']*
    )["']""",
    re.IGNORECASE | re.VERBOSE,
)

# Slugs inside Nuxt/Next SSR payloads (e.g. "ویدیو-کاربرد-برنامه-اکسل-چیست")
_NUXT_SLUG_RE = re.compile(r'["\'](ویدیو-[^"\']{2,120})["\']')
_MEDIA_URL_RE = re.compile(
    r'https?://[^"\'\s\\]+?(?:\.mp4|\.m3u8)[^"\'\s\\]*',
    re.IGNORECASE,
)


def extract_nuxt_lesson_slugs(html: str) -> List[str]:
    """Extract Maktabkhooneh lesson slugs from an SSR/Nuxt payload.

    Parameters
    ----------
    html : str
        Course page HTML.

    Returns
    -------
    list of str
        Unique lesson slugs in document order.
    """
    found: List[str] = []
    for match in _NUXT_SLUG_RE.finditer(html or ""):
        slug = match.group(1).strip()
        if slug not in found:
            found.append(slug)
    return found


def extract_media_urls(html: str) -> List[str]:
    """Extract direct media file URLs (mp4/m3u8) from page HTML.

    Useful for free preview samples embedded in course pages.

    Parameters
    ----------
    html : str
        Page HTML.

    Returns
    -------
    list of str
        Unique media URLs.
    """
    found: List[str] = []
    for match in _MEDIA_URL_RE.finditer(html or ""):
        url = match.group(0).replace("\\u0026", "&").replace("\\/", "/")
        if url not in found:
            found.append(url)
    return found


def extract_lesson_hrefs(html: str, base_url: str) -> List[str]:
    """Extract unique lesson/video hrefs from a course HTML page.

    Falls back to Maktabkhooneh Nuxt SSR payload slugs when the page has
    no ``href`` lesson links (SPA/SSR course shell).

    Parameters
    ----------
    html : str
        Raw HTML of the course page.
    base_url : str
        Absolute URL used to resolve relative links.

    Returns
    -------
    list of str
        Absolute lesson URLs in document order, de-duplicated.
    """
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
    """Check whether *url* is a Maktabkhooneh link.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` for maktabkhooneh.org hosts.
    """
    return host_matches(url_host(url), _MAKTAB_HOSTS)


def is_faradars_url(url: str) -> bool:
    """Check whether *url* is a Faradars link.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` for faradars.org hosts.
    """
    return host_matches(url_host(url), _FARADARS_HOSTS)


def is_education_url(url: str) -> bool:
    """Check whether *url* is Maktabkhooneh or Faradars.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` if the host matches a supported education platform.
    """
    return is_maktabkhooneh_url(url) or is_faradars_url(url)


def platform_name(url: str) -> str:
    """Return a human-readable platform label for *url*.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    str
        ``Maktabkhooneh``, ``Faradars``, or ``Unknown``.
    """
    if is_maktabkhooneh_url(url):
        return "Maktabkhooneh"
    if is_faradars_url(url):
        return "Faradars"
    return "Unknown"


def _fetch_html(url: str) -> str:
    """Fetch page HTML using the active proxy if configured.

    Parameters
    ----------
    url : str
        Page URL.

    Returns
    -------
    str
        Response text (empty string on failure).
    """
    import requests

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
    try:
        resp = requests.get(
            url, timeout=20, proxies=proxies, headers=headers, allow_redirects=True
        )
        resp.raise_for_status()
        return resp.text or ""
    except Exception:
        return ""


def parse_course_outline(url: str, html: Optional[str] = None) -> CourseOutline:
    """Parse a course landing page into an outline.

    Parameters
    ----------
    url : str
        Course URL.
    html : str, optional
        Pre-fetched HTML; fetched when omitted.

    Returns
    -------
    CourseOutline
        Platform, title, and lesson list (may be empty when the page is
        behind login or the markup changed).
    """
    platform = platform_name(url)
    if html is None:
        html = _fetch_html(url)

    title = ""
    title_match = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        html or "",
        re.IGNORECASE,
    )
    if not title_match:
        title_match = re.search(r"<title>([^<]+)</title>", html or "", re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    hrefs = extract_lesson_hrefs(html or "", url)
    lessons = [
        CourseLesson(title=href.rsplit("/", 1)[-1][:80] or f"lesson-{i + 1}", url=href, index=i)
        for i, href in enumerate(hrefs)
    ]
    return CourseOutline(platform=platform, course_url=url, title=title, lessons=lessons)


def download_education_course(
    url: str,
    out_folder: Path,
    *,
    fmt: str = "bestvideo+bestaudio/best",
    max_lessons: Optional[int] = None,
) -> bool:
    """Download lessons from an education course URL.

    Single lesson URLs go straight to yt-dlp. Course landing pages list
    lessons first; each lesson is downloaded with the same format.

    Parameters
    ----------
    url : str
        Course or lesson URL.
    out_folder : pathlib.Path
        Destination directory.
    fmt : str, optional
        yt-dlp format selector.
    max_lessons : int, optional
        Cap on lessons processed from a course page.

    Returns
    -------
    bool
        ``True`` if every attempted lesson succeeded (or a single lesson
        succeeded). ``False`` otherwise.
    """
    from smart_dl.extractors.youtube import download_yt, get_yt_formats
    from smart_dl.utils import is_http_url

    print_section(platform_name(url) + " course", "\U0001f393")
    if not is_http_url(url):
        error("Not a valid URL.")
        return False

    out_folder.mkdir(parents=True, exist_ok=True)

    # Prefer cookies for authorized streams.
    from smart_dl.core.cookies import get_cookie_browser

    browser = get_cookie_browser()
    if browser:
        info("Using cookies from: " + browser.capitalize())
    else:
        warn(
            "No browser cookie source set. Paid courses need a logged-in "
            "session — press C at the URL prompt after a bot/login error."
        )

    # Direct lesson / single media URL: try yt-dlp formats first.
    info_dict = get_yt_formats(url)
    if info_dict and info_dict.get("formats"):
        return download_yt(url, out_folder, fmt, False)

    outline = parse_course_outline(url)
    if not outline.lessons:
        error("No lessons found. You may need to log in, or the page layout changed.")
        if outline.title:
            info("Page title: " + outline.title[:80])
        return False

    lessons: Iterable[CourseLesson] = outline.lessons
    if max_lessons is not None:
        lessons = list(outline.lessons)[: max(0, int(max_lessons))]

    info(f"Found {len(outline)} lesson(s)" + (f" — {outline.title[:60]}" if outline.title else ""))
    ok_count = 0
    fail_count = 0
    for lesson in lessons:
        info(f"[{lesson.index + 1}/{len(outline)}] {lesson.title[:60]}")
        info_dict = get_yt_formats(lesson.url)
        if not info_dict:
            warn("Could not extract lesson (login required?).")
            fail_count += 1
            continue
        # Bulk course download uses one shared format (no per-lesson menu).
        if download_yt(lesson.url, out_folder, fmt, False):
            ok_count += 1
        else:
            fail_count += 1

    success(f"Downloaded {ok_count}/{ok_count + fail_count} lesson(s) → {out_folder}")
    return fail_count == 0 and ok_count > 0
