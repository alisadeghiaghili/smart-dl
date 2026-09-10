"""Education platform extractors — Maktabkhooneh, Faradars, Coursera.

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
    "coursera_lecture_url",
    "download_education_course",
    "expand_coursera_outline_with_items",
    "extract_lesson_hrefs",
    "fetch_coursera_module_items",
    "is_coursera_url",
    "is_education_url",
    "is_faradars_url",
    "is_maktabkhooneh_url",
    "platform_name",
]

_MAKTAB_HOSTS = ("maktabkhooneh.org", "www.maktabkhooneh.org")
_FARADARS_HOSTS = ("faradars.org", "www.faradars.org")
_COURSERA_HOSTS = ("coursera.org", "www.coursera.org")

# Lesson / video path fragments used by the supported platforms.
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


def is_coursera_url(url: str) -> bool:
    """Check whether *url* is a Coursera link.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` for coursera.org hosts.
    """
    return host_matches(url_host(url), _COURSERA_HOSTS)


def is_education_url(url: str) -> bool:
    """Check whether *url* is Maktabkhooneh, Faradars, or Coursera.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` if the host matches a supported education platform.
    """
    return is_maktabkhooneh_url(url) or is_faradars_url(url) or is_coursera_url(url)


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
    if is_coursera_url(url):
        return "Coursera"
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


def _coursera_course_slug(url: str) -> str:
    """Extract the course slug from a Coursera learn URL.

    Parameters
    ----------
    url : str
        e.g. ``https://www.coursera.org/learn/machine-learning``

    Returns
    -------
    str
        Slug, or ``""`` when the path is not a course.
    """
    path = urlparse(url or "").path
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "learn":
        return parts[1]
    return ""


def parse_coursera_syllabus(url: str) -> CourseOutline:
    """Fetch a Coursera course title and weekly modules via public API.

    Individual video items require enrollment/auth and are not listed
    anonymously. Modules are returned as high-level outline entries.

    Parameters
    ----------
    url : str
        Course URL (``/learn/<slug>``).

    Returns
    -------
    CourseOutline
        Title and module lessons; empty lessons on failure.
    """
    slug = _coursera_course_slug(url)
    if not slug:
        return CourseOutline(platform="Coursera", course_url=url)

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
        "Accept": "application/json",
    }
    base = "https://www.coursera.org"
    title = ""
    lessons: List[CourseLesson] = []

    try:
        meta = requests.get(
            f"{base}/api/courses.v1?q=slug&slug={slug}",
            headers=headers,
            proxies=proxies,
            timeout=20,
        )
        if meta.status_code == 200:
            elements = meta.json().get("elements") or []
            if elements:
                title = (elements[0].get("name") or "").strip()
    except Exception:
        pass

    try:
        mats = requests.get(
            f"{base}/api/onDemandCourseMaterials.v2?q=slug&slug={slug}&includes=modules",
            headers=headers,
            proxies=proxies,
            timeout=20,
        )
        if mats.status_code == 200:
            linked = mats.json().get("linked") or {}
            modules = linked.get("onDemandCourseMaterialModules.v1") or []
            for index, module in enumerate(modules):
                name = (module.get("name") or f"module-{index + 1}").strip()
                # Outline entry points at the course page; full item URLs
                # need enrollment + cookies.
                lessons.append(
                    CourseLesson(title=name[:120], url=url, index=index)
                )
    except Exception:
        pass

    return CourseOutline(
        platform="Coursera",
        course_url=url,
        title=title,
        lessons=lessons,
    )


def coursera_lecture_url(slug: str, item_id: str) -> str:
    """Build a Coursera lecture URL from a course slug and item id.

    Parameters
    ----------
    slug : str
        Course slug (e.g. ``machine-learning``).
    item_id : str
        On-demand material item id.

    Returns
    -------
    str
        ``https://www.coursera.org/learn/{slug}/lecture/{item_id}``
    """
    slug = (slug or "").strip("/")
    item_id = (item_id or "").strip()
    return f"https://www.coursera.org/learn/{slug}/lecture/{item_id}"


def fetch_coursera_module_items(
    course_id: str,
    module_id: str,
    session=None,
) -> List[dict]:
    """Fetch material items for one Coursera module.

    Requires an authenticated session (browser cookies) for most courses.

    Parameters
    ----------
    course_id : str
        On-demand course id from ``courses.v1``.
    module_id : str
        Module id from ``onDemandCourseMaterialModules.v1``.
    session : requests.Session, optional
        Session with cookies; a default session is used when omitted.

    Returns
    -------
    list of dict
        Raw item objects with ``id``, ``name``, ``typeName`` when present.
    """
    import requests

    if session is None:
        session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
    url = (
        "https://www.coursera.org/api/onDemandCourseMaterialItems.v2"
        f"?courseId={course_id}&moduleId={module_id}"
    )
    try:
        resp = session.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return []
        elements = resp.json().get("elements") or []
        return [e for e in elements if isinstance(e, dict)]
    except Exception:
        return []


def expand_coursera_outline_with_items(
    outline: CourseOutline,
    *,
    session=None,
    slug: str = "",
) -> CourseOutline:
    """Replace weekly module placeholders with lecture URLs when possible.

    When *session* is authenticated, module lessons that still point at the
    course landing page are expanded using the items API. Anonymous sessions
    leave the outline unchanged.

    Parameters
    ----------
    outline : CourseOutline
        Outline from :func:`parse_coursera_syllabus`.
    session : requests.Session, optional
        Cookie-authenticated session.
    slug : str, optional
        Course slug for lecture URL building.

    Returns
    -------
    CourseOutline
        Possibly expanded outline (same object type, new lessons list).
    """
    if session is None or not slug:
        return outline

    # Module ids are not stored on CourseLesson; re-fetch materials.

    from smart_dl.core.proxy import get_current_proxy

    proxy = get_current_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        mats = session.get(
            f"https://www.coursera.org/api/onDemandCourseMaterials.v2"
            f"?q=slug&slug={slug}&includes=modules",
            headers=headers,
            proxies=proxies,
            timeout=20,
        )
        if mats.status_code != 200:
            return outline
        payload = mats.json()
        elements = payload.get("elements") or []
        course_id = ""
        if elements and isinstance(elements[0], dict):
            course_id = str(elements[0].get("id") or "")
        modules = (payload.get("linked") or {}).get(
            "onDemandCourseMaterialModules.v1"
        ) or []
    except Exception:
        return outline

    lessons: List[CourseLesson] = []
    index = 0
    for module in modules:
        module_id = module.get("id") or ""
        module_name = (module.get("name") or "").strip()
        items = fetch_coursera_module_items(
            course_id,
            module_id,
            session=session,
        )
        if not items:
            lessons.append(
                CourseLesson(
                    title=module_name or f"module-{index + 1}",
                    url=outline.course_url,
                    index=index,
                )
            )
            index += 1
            continue
        for item in items:
            item_id = str(item.get("id") or "")
            name = (item.get("name") or item_id or "item").strip()
            lecture = (
                coursera_lecture_url(slug, item_id) if item_id else outline.course_url
            )
            lessons.append(CourseLesson(title=name[:120], url=lecture, index=index))
            index += 1

    if not lessons:
        return outline
    return CourseOutline(
        platform=outline.platform,
        course_url=outline.course_url,
        title=outline.title,
        lessons=lessons,
    )


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

    # Live Coursera course pages are SPA shells; use the public syllabus API
    # unless the caller already supplied HTML (unit tests / cached markup).
    if platform == "Coursera" and html is None:
        outline = parse_coursera_syllabus(url)
        if outline.lessons or outline.title:
            from smart_dl.core.browser_cookies import session_with_browser_cookies

            slug = _coursera_course_slug(url)
            auth = session_with_browser_cookies(domains=["coursera.org"])
            return expand_coursera_outline_with_items(
                outline, session=auth, slug=slug
            )

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
