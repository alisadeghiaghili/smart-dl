"""Unit tests for Coursera lecture URLs and cookie-based expansion."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.education import (  # noqa: E402
    CourseOutline,
    coursera_lecture_url,
    expand_coursera_outline_with_items,
    fetch_coursera_module_items,
)


class TestLectureUrl:
    def test_builds_url(self) -> None:
        url = coursera_lecture_url("machine-learning", "abc123")
        assert url == "https://www.coursera.org/learn/machine-learning/lecture/abc123"

    def test_strips_slashes(self) -> None:
        url = coursera_lecture_url("/machine-learning/", "abc")
        assert url == "https://www.coursera.org/learn/machine-learning/lecture/abc"


class TestFetchModuleItems:
    def test_returns_elements(self) -> None:
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "elements": [
                {"id": "i1", "name": "Video 1", "typeName": "lecture"},
                {"id": "i2", "name": "Quiz", "typeName": "quiz"},
            ]
        }
        session.get.return_value = resp
        items = fetch_coursera_module_items("CID", "MOD", session=session)
        assert len(items) == 2
        assert items[0]["id"] == "i1"

    def test_http_error_returns_empty(self) -> None:
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 403
        session.get.return_value = resp
        assert fetch_coursera_module_items("CID", "MOD", session=session) == []


class TestExpandOutline:
    def test_no_session_returns_same_outline(self) -> None:
        outline = CourseOutline(platform="Coursera", course_url="https://www.coursera.org/learn/x")
        result = expand_coursera_outline_with_items(outline, session=None, slug="x")
        assert result is outline

    def test_expands_when_items_returned(self) -> None:
        outline = CourseOutline(
            platform="Coursera",
            course_url="https://www.coursera.org/learn/ml",
            title="ML",
            lessons=[],
        )
        session = MagicMock()

        def get(url, **kwargs):
            resp = MagicMock()
            if "onDemandCourseMaterials" in url:
                resp.status_code = 200
                resp.json.return_value = {
                    "elements": [{"id": "CID"}],
                    "linked": {
                        "onDemandCourseMaterialModules.v1": [
                            {"id": "M1", "name": "Week 1", "courseId": "CID"}
                        ]
                    },
                }
            else:
                resp.status_code = 200
                resp.json.return_value = {
                    "elements": [{"id": "ITEM1", "name": "Welcome", "typeName": "lecture"}]
                }
            return resp

        session.get.side_effect = get
        result = expand_coursera_outline_with_items(outline, session=session, slug="ml")
        assert len(result) == 1
        assert result.lessons[0].url.endswith("/lecture/ITEM1")
        assert result.lessons[0].title == "Welcome"
