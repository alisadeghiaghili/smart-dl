"""Coursera extractor implementation."""

from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

from smart_dl.extractors.education.common import CourseLesson, CourseOutline


def coursera_course_slug(url: str) -> str:
    """Extract the course slug from a Coursera URL."""
    path = urlparse(url or "").path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "learn":
        return parts[1]
    if len(parts) >= 1:
        return parts[0]
    return ""


def coursera_lecture_url(slug: str, item_id: str) -> str:
    """Build a Coursera lecture URL from a course slug and item id."""
    slug = (slug or "").strip("/")
    item_id = (item_id or "").strip()
    return f"https://www.coursera.org/learn/{slug}/lecture/{item_id}"


def parse_coursera_syllabus(url: str) -> CourseOutline:
    """Fetch publicly visible course syllabus from Coursera API."""
    slug = coursera_course_slug(url)
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
                lessons.append(CourseLesson(title=name[:120], url=url, index=index))
    except Exception:
        pass

    return CourseOutline(platform="Coursera", course_url=url, title=title, lessons=lessons)


def fetch_coursera_module_items(
    course_id: str,
    module_id: str,
    session=None,
) -> List[dict]:
    """Fetch material items for one Coursera module."""
    if not course_id or not module_id:
        return []

    import requests

    from smart_dl.core.proxy import get_current_proxy

    sess = session or requests.Session()
    proxy = get_current_proxy()
    if proxy and not session:
        sess.proxies.update({"http": proxy, "https": proxy})

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
    url = (
        f"https://www.coursera.org/api/onDemandCourseMaterialItems.v1/"
        f"?courseId={course_id}&moduleId={module_id}&includes=items"
    )
    try:
        resp = sess.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = data.get("elements") or (data.get("linked") or {}).get("onDemandCourseMaterialItems.v1") or []
        return [it for it in items if isinstance(it, dict)]
    except Exception:
        return []


def expand_coursera_outline_with_items(
    outline: CourseOutline,
    session=None,
    slug: Optional[str] = None,
) -> CourseOutline:
    """Expand module-level Coursera lessons to lecture items using session cookies."""
    if session is None or not slug:
        return outline

    from smart_dl.core.proxy import get_current_proxy

    proxy = get_current_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        mats = session.get(
            f"https://www.coursera.org/api/onDemandCourseMaterials.v2/?q=slug&slug={slug}&includes=modules",
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
            name = (item.get("name") or item.get("title") or item_id or "item").strip()
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
