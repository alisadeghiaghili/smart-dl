"""Education platform extractors package — Maktabkhooneh, Faradars, Coursera."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

from smart_dl.extractors.education.common import (
    CourseLesson,
    CourseOutline,
    extract_lesson_hrefs,
    extract_media_urls,
    extract_nuxt_lesson_slugs,
    fetch_html,
    is_coursera_url,
    is_education_url,
    is_faradars_url,
    is_maktabkhooneh_url,
    platform_name,
)
from smart_dl.extractors.education.coursera import (
    coursera_course_slug,
    coursera_lecture_url,
    expand_coursera_outline_with_items,
    fetch_coursera_module_items,
    parse_coursera_syllabus,
)
from smart_dl.extractors.education.faradars import (
    extract_faradars_course_paths,
    extract_next_data_title,
    parse_faradars_outline,
)
from smart_dl.extractors.education.maktabkhooneh import parse_maktabkhooneh_outline
from smart_dl.ui import error, info, print_section, success, warn

__all__ = [
    "CourseLesson",
    "CourseOutline",
    "coursera_lecture_url",
    "download_education_course",
    "expand_coursera_outline_with_items",
    "extract_faradars_course_paths",
    "extract_lesson_hrefs",
    "extract_media_urls",
    "extract_next_data_title",
    "extract_nuxt_lesson_slugs",
    "fetch_coursera_module_items",
    "is_coursera_url",
    "is_education_url",
    "is_faradars_url",
    "is_maktabkhooneh_url",
    "parse_course_outline",
    "parse_coursera_syllabus",
    "parse_faradars_outline",
    "parse_maktabkhooneh_outline",
    "platform_name",
]


def _looks_like_lesson_url(url: str) -> bool:
    return any(
        marker in urlparse(url or "").path.lower()
        for marker in ("/lecture/", "/lesson/", "/ویدیو-", "/video-")
    )


_fetch_html = fetch_html
_coursera_course_slug = coursera_course_slug


def parse_course_outline(url: str, html: Optional[str] = None) -> CourseOutline:
    """Parse a course landing page into an outline."""
    platform = platform_name(url)

    if html is None:
        html = _fetch_html(url)

    if platform == "Coursera":
        # If HTML has explicit lecture links (e.g. test fixture or rendered page), extract them
        if html:
            hrefs = extract_lesson_hrefs(html, url)
            if hrefs:
                import re
                title = ""
                title_match = re.search(
                    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
                    html,
                    re.IGNORECASE,
                ) or re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                lessons = [
                    CourseLesson(
                        title=href.rsplit("/", 1)[-1][:80] or f"lesson-{i + 1}",
                        url=href,
                        index=i,
                    )
                    for i, href in enumerate(hrefs)
                ]
                return CourseOutline(
                    platform=platform, course_url=url, title=title, lessons=lessons
                )

        outline = parse_coursera_syllabus(url)
        if outline.lessons or outline.title:
            from smart_dl.core.browser_cookies import session_with_browser_cookies

            slug = coursera_course_slug(url)
            auth = session_with_browser_cookies(domains=["coursera.org"])
            return expand_coursera_outline_with_items(
                outline, session=auth, slug=slug
            )
        return outline

    if platform == "Maktabkhooneh":
        return parse_maktabkhooneh_outline(url, html=html)
    if platform == "Faradars":
        return parse_faradars_outline(url, html=html)

    # General fallback
    if html is None:
        html = fetch_html(url)
    import re
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
    """Download lessons from an education course URL."""
    from smart_dl.utils import is_http_url

    print_section(platform_name(url) + " course", "🎓")
    if not is_http_url(url):
        error("Not a valid URL.")
        return False

    out_folder.mkdir(parents=True, exist_ok=True)

    from smart_dl.core.cookies import get_cookie_browser

    browser = get_cookie_browser()
    if browser:
        info("Using cookies from: " + browser.capitalize())
    else:
        warn(
            "No browser cookie source set. Paid courses need a logged-in "
            "session — press C at the URL prompt after a bot/login error."
        )

    from smart_dl.extractors.youtube import download_yt, get_yt_formats

    if _looks_like_lesson_url(url):
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
        if not lesson.url or lesson.url.rstrip("/") == url.rstrip("/"):
            info(f"[{lesson.index + 1}/{len(outline)}] {lesson.title[:60]} — outline only")
            continue
        info(f"[{lesson.index + 1}/{len(outline)}] {lesson.title[:60]}")
        info_dict = get_yt_formats(lesson.url)
        if not info_dict:
            warn("Could not extract lesson (login required?).")
            fail_count += 1
            continue
        if download_yt(lesson.url, out_folder, fmt, False):
            ok_count += 1
        else:
            fail_count += 1

    attempted = ok_count + fail_count
    if attempted == 0:
        warn(
            "No downloadable lecture URLs yet — only outline modules. "
            "Enroll/log in, then re-run with cookies configured."
        )
        return False
    success(f"Downloaded {ok_count}/{attempted} lesson(s) → {out_folder}")
    return fail_count == 0 and ok_count > 0
