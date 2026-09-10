"""Unit tests for Coursera education extractor support."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.education import (  # noqa: E402
    extract_lesson_hrefs,
    is_coursera_url,
    is_education_url,
    parse_course_outline,
    platform_name,
)

SAMPLE_COURSERA_HTML = """
<html>
<head><title>Machine Learning | Coursera</title>
<meta property="og:title" content="Machine Learning Specialization" />
</head>
<body>
<a href="/learn/machine-learning/lecture/video-1-intro">Introduction</a>
<a href="/learn/machine-learning/lecture/video-2-regression">Regression</a>
<a href="/lecture/standalone-quiz-1">Quiz</a>
<a href="/learn/machine-learning">Course home</a>
</body>
</html>
"""


class TestCourseraDetection:
    def test_hosts(self) -> None:
        assert is_coursera_url("https://www.coursera.org/learn/python") is True
        assert is_coursera_url("https://coursera.org/learn/python") is True
        assert is_coursera_url("https://www.coursera.org/specializations/data") is True

    def test_rejects_lookalike(self) -> None:
        assert is_coursera_url("https://coursera.org.evil.com/x") is False
        assert is_coursera_url("https://notcoursera.org/x") is False

    def test_education_url_includes_coursera(self) -> None:
        assert is_education_url("https://www.coursera.org/learn/ml") is True
        assert platform_name("https://www.coursera.org/learn/ml") == "Coursera"


class TestCourseraOutline:
    def test_lecture_hrefs(self) -> None:
        hrefs = extract_lesson_hrefs(
            SAMPLE_COURSERA_HTML, "https://www.coursera.org/learn/machine-learning"
        )
        assert len(hrefs) >= 2
        assert any("/lecture/video-1-intro" in h for h in hrefs)
        assert all(h.startswith("https://www.coursera.org/") for h in hrefs)

    def test_html_outline_when_html_supplied(self) -> None:
        outline = parse_course_outline(
            "https://www.coursera.org/learn/machine-learning",
            html=SAMPLE_COURSERA_HTML,
        )
        assert outline.platform == "Coursera"
        assert "Machine Learning" in outline.title
        assert len(outline) >= 2

    def test_course_slug_parser(self) -> None:
        from smart_dl.extractors.education import _coursera_course_slug

        assert (
            _coursera_course_slug("https://www.coursera.org/learn/machine-learning")
            == "machine-learning"
        )
        assert (
            _coursera_course_slug(
                "https://www.coursera.org/learn/machine-learning/lecture/abc"
            )
            == "machine-learning"
        )
        assert _coursera_course_slug("https://www.coursera.org/") == ""

    def test_syllabus_api_live(self) -> None:
        """Live public-API check (weekly modules for a known course)."""
        outline = parse_course_outline(
            "https://www.coursera.org/learn/machine-learning"
        )
        assert outline.platform == "Coursera"
        assert outline.title
        assert "Machine Learning" in outline.title or "Regression" in outline.title
        assert len(outline) >= 1
