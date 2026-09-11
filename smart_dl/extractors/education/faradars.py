"""Faradars extractor implementation."""

from __future__ import annotations

import json
import re
from typing import List, Optional
from urllib.parse import urlparse

from smart_dl.extractors.education.common import (
    CourseLesson,
    CourseOutline,
    extract_lesson_hrefs,
    fetch_html,
)


def extract_faradars_course_paths(html: str) -> List[str]:
    """Extract unique Faradars course-like paths from page HTML."""
    found: List[str] = []
    for match in re.finditer(
        r'href=["\'](/(?:fv[0-9][^"\']*|how-to-learn/[^"\']+|courses?/[^"\']+))["\']',
        html or "",
        re.I,
    ):
        path = match.group(1).rstrip("\\").strip()
        if path and path not in found:
            found.append(path)
    return found


def extract_next_data_title(html: str) -> str:
    """Extract a page title from a Next.js __NEXT_DATA__ payload."""
    match = re.search(
        r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html or "",
        re.S,
    )
    if not match:
        return ""
    try:
        data = json.loads(match.group(1))
    except Exception:
        return ""
    page = (data.get("props") or {}).get("pageProps") or {}
    for key in ("title", "courseTitle", "name"):
        value = page.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("course", "product", "data"):
        node = page.get(key)
        if isinstance(node, dict):
            for inner in ("title", "name"):
                value = node.get(inner)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return ""


def parse_faradars_outline(url: str, html: Optional[str] = None) -> CourseOutline:
    """Parse a Faradars course landing page into an outline."""
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
    if not title:
        title = extract_next_data_title(html or "")
        if not title and html:
            try:
                from smart_dl.extractors.faradars_next import (
                    fetch_faradars_page_json,
                    title_from_next_json,
                )

                title = title_from_next_json(fetch_faradars_page_json(url, html=html))
            except Exception:
                pass

    hrefs = extract_lesson_hrefs(html or "", url)
    if not hrefs:
        base = "{0.scheme}://{0.netloc}".format(urlparse(url))
        hrefs = [base + path for path in extract_faradars_course_paths(html or "")]

    lessons = [
        CourseLesson(
            title=href.rsplit("/", 1)[-1][:80] or f"lesson-{i + 1}",
            url=href,
            index=i,
        )
        for i, href in enumerate(hrefs)
    ]
    return CourseOutline(platform="Faradars", course_url=url, title=title, lessons=lessons)
