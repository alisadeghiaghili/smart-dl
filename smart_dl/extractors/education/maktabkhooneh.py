"""Maktabkhooneh extractor implementation."""

from __future__ import annotations

import re
from typing import Optional

from smart_dl.extractors.education.common import (
    CourseLesson,
    CourseOutline,
    extract_lesson_hrefs,
    fetch_html,
)


def parse_maktabkhooneh_outline(url: str, html: Optional[str] = None) -> CourseOutline:
    """Parse a Maktabkhooneh course landing page into an outline."""
    if html is None:
        html = fetch_html(url)

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
        CourseLesson(
            title=href.rsplit("/", 1)[-1][:80] or f"lesson-{i + 1}",
            url=href,
            index=i,
        )
        for i, href in enumerate(hrefs)
    ]
    return CourseOutline(platform="Maktabkhooneh", course_url=url, title=title, lessons=lessons)
