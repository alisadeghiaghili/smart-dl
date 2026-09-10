"""Unit tests for Faradars Next.js title extraction and lesson skip logic."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.education import (  # noqa: E402
    CourseOutline,
    extract_next_data_title,
    parse_course_outline,
)

NEXT_HTML = """
<script id="__NEXT_DATA__" type="application/json">
{"props":{"pageProps":{"title":"آموزش پایتون کاربردی"}}}
</script>
"""


class TestNextDataTitle:
    def test_reads_title(self) -> None:
        assert extract_next_data_title(NEXT_HTML) == "آموزش پایتون کاربردی"

    def test_missing_payload(self) -> None:
        assert extract_next_data_title("<html></html>") == ""

    def test_invalid_json(self) -> None:
        assert extract_next_data_title(
            '<script id="__NEXT_DATA__" type="application/json">{oops</script>'
        ) == ""


class TestFaradarsOutlineTitle:
    def test_falls_back_to_next_data(self) -> None:
        outline = parse_course_outline(
            "https://faradars.org/fv1234-python", html=NEXT_HTML
        )
        assert outline.platform == "Faradars"
        assert outline.title == "آموزش پایتون کاربردی"
        assert len(outline) == 0


class TestPlaceholdersNotDownloaded:
    def test_download_skips_outline_only_urls(self, tmp_path, monkeypatch) -> None:
        import smart_dl.extractors.education as edu

        outline = CourseOutline(
            platform="Coursera",
            course_url="https://www.coursera.org/learn/ml",
            title="ML",
            lessons=[],
        )
        # lesson that points at the course page itself
        from smart_dl.extractors.education import CourseLesson

        outline.lessons.append(
            CourseLesson(title="Week 1", url=outline.course_url, index=0)
        )
        monkeypatch.setattr(
            edu, "parse_course_outline", lambda url, html=None: outline
        )
        import smart_dl.extractors.youtube as yt

        monkeypatch.setattr(yt, "get_yt_formats", lambda url: None)
        monkeypatch.setattr(yt, "download_yt", lambda *a, **k: False)

        ok = edu.download_education_course(
            "https://www.coursera.org/learn/ml", tmp_path
        )
        assert ok is False
