"""Unit tests for education platform extractors."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.education import (  # noqa: E402
    extract_lesson_hrefs,
    is_faradars_url,
    is_maktabkhooneh_url,
    parse_course_outline,
    platform_name,
)

SAMPLE_MK_HTML = """
<html><head><title>آموزش پایتون | مکتب‌خونه</title>
<meta property="og:title" content="آموزش برنامه‌نویسی پایتون" />
</head><body>
<a class="group" href="/course/python-mk123/ویدیو-مقدمه">مقدمه</a>
<a class="group" href="/course/python-mk123/ویدیو-متغیرها">متغیرها</a>
<a class="group" href="https://maktabkhooneh.org/course/python-mk123/ویدیو-حلقه‌ها">حلقه‌ها</a>
<a href="/course/python-mk123/ویدیو-مقدمه">duplicate</a>
<a href="/about">not a lesson</a>
</body></html>
"""

SAMPLE_FARADARS_HTML = """
<html><head><title>آموزش متلب | فرادرس</title></head><body>
<a href="/fv1234-matlab/lesson/01-intro">درس ۱</a>
<a href="/fv1234-matlab/lesson/02-vars">درس ۲</a>
</body></html>
"""


class TestUrlDetection:
    def test_maktabkhooneh_hosts(self) -> None:
        assert is_maktabkhooneh_url("https://maktabkhooneh.org/course/foo/") is True
        assert is_maktabkhooneh_url("https://www.maktabkhooneh.org/course/foo/") is True

    def test_faradars_hosts(self) -> None:
        assert is_faradars_url("https://faradars.org/fv1234-title") is True
        assert is_faradars_url("https://www.faradars.org/fv1234-title") is True

    def test_rejects_lookalikes(self) -> None:
        assert is_maktabkhooneh_url("https://maktabkhooneh.org.evil.com/x") is False
        assert is_faradars_url("https://notfaradars.org/x") is False

    def test_platform_name(self) -> None:
        assert platform_name("https://maktabkhooneh.org/course/x/") == "Maktabkhooneh"
        assert platform_name("https://faradars.org/fv1") == "Faradars"
        assert platform_name("https://youtube.com/watch?v=a") == "Unknown"


class TestLessonHrefs:
    def test_extracts_unique_absolute_urls(self) -> None:
        hrefs = extract_lesson_hrefs(SAMPLE_MK_HTML, "https://maktabkhooneh.org/course/python-mk123/")
        assert len(hrefs) == 3
        assert all(h.startswith("https://maktabkhooneh.org/") for h in hrefs)
        assert hrefs[0].endswith("ویدیو-مقدمه")

    def test_faradars_lesson_pattern(self) -> None:
        hrefs = extract_lesson_hrefs(
            SAMPLE_FARADARS_HTML, "https://faradars.org/fv1234-matlab"
        )
        assert len(hrefs) == 2
        assert "/lesson/01-intro" in hrefs[0]

    def test_empty_html(self) -> None:
        assert extract_lesson_hrefs("", "https://example.com") == []


class TestParseOutline:
    def test_mk_title_and_lessons(self) -> None:
        outline = parse_course_outline(
            "https://maktabkhooneh.org/course/python-mk123/", html=SAMPLE_MK_HTML
        )
        assert outline.platform == "Maktabkhooneh"
        assert "پایتون" in outline.title
        assert len(outline) == 3

    def test_faradars_outline(self) -> None:
        outline = parse_course_outline(
            "https://faradars.org/fv1234-matlab", html=SAMPLE_FARADARS_HTML
        )
        assert outline.platform == "Faradars"
        assert len(outline) == 2


SAMPLE_MK_NUXT = """
<script type="application/json" data-nuxt-data="nuxt-app" id="__NUXT_DATA__">
["ویدیو-کاربرد-برنامه-اکسل-چیست","ویدیو-آغاز-فرمولنویسی-اکسل",
"https://cdn.maktabkhooneh.org/videos/123.mp4?expire=1&token=abc",
"https://cdn.maktabkhooneh.org/videos/hq123.mp4?expire=1&token=def"]
</script>
"""


class TestNuxtPayload:
    def test_slugs_from_payload(self) -> None:
        from smart_dl.extractors.education import extract_nuxt_lesson_slugs

        slugs = extract_nuxt_lesson_slugs(SAMPLE_MK_NUXT)
        assert slugs[0] == "ویدیو-کاربرد-برنامه-اکسل-چیست"
        assert len(slugs) == 2

    def test_media_urls_from_payload(self) -> None:
        from smart_dl.extractors.education import extract_media_urls

        urls = extract_media_urls(SAMPLE_MK_NUXT)
        assert len(urls) == 2
        assert urls[0].startswith("https://cdn.maktabkhooneh.org/videos/")

    def test_outline_from_nuxt_when_no_hrefs(self) -> None:
        outline = parse_course_outline(
            "https://maktabkhooneh.org/course/excel-mk8334/",
            html=SAMPLE_MK_NUXT,
        )
        assert len(outline) == 2
        assert "excel-mk8334/ویدیو-کاربرد-برنامه-اکسل-چیست" in outline.lessons[0].url


class TestFetchHtmlWithCookies:
    def test_fetch_html_uses_browser_cookies(self) -> None:
        from unittest.mock import MagicMock, patch

        from smart_dl.extractors.education import _fetch_html

        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>authenticated content</body></html>"
        mock_session.get.return_value = mock_resp

        with patch("smart_dl.core.cookies.get_cookie_browser", return_value="firefox"), \
             patch("smart_dl.core.browser_cookies.session_with_browser_cookies", return_value=mock_session) as mock_swbc, \
             patch("smart_dl.core.proxy.get_current_proxy", return_value="socks5h://127.0.0.1:10808"):
            html = _fetch_html("https://maktabkhooneh.org/course/python-mk123/")
            assert html == "<html><body>authenticated content</body></html>"
            mock_swbc.assert_called_once_with("firefox", domains=["maktabkhooneh.org"])
            mock_session.get.assert_called_once()
            assert mock_session.proxies.update.called

    def test_fetch_html_without_browser_cookies(self) -> None:
        from unittest.mock import MagicMock, patch

        from smart_dl.extractors.education import _fetch_html

        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "<html>public</html>"
        mock_session.get.return_value = mock_resp

        with patch("smart_dl.core.cookies.get_cookie_browser", return_value=None), \
             patch("requests.Session", return_value=mock_session):
            html = _fetch_html("https://maktabkhooneh.org/course/python-mk123/")
            assert html == "<html>public</html>"
            mock_session.get.assert_called_once()

    def test_maktabkhooneh_outline_with_cookies(self) -> None:
        from unittest.mock import patch

        from smart_dl.extractors.education import parse_course_outline

        mock_html = """
        <html><head><title>آموزش پایتون پیشرفته</title></head><body>
        <a class="group" href="/course/python-adv/ویدیو-۱">درس اول</a>
        <a class="group" href="/course/python-adv/ویدیو-۲">درس دوم</a>
        </body></html>
        """
        with patch("smart_dl.extractors.education._fetch_html", return_value=mock_html):
            outline = parse_course_outline("https://maktabkhooneh.org/course/python-adv/")
            assert len(outline) == 2
            assert outline.platform == "Maktabkhooneh"
            assert "پایتون پیشرفته" in outline.title

