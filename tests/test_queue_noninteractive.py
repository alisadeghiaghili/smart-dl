"""Unit tests for v3.9.1 bugfixes."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"


class TestEducationLandingSkipsYtDlp:
    def test_course_landing_goes_to_outline(self, tmp_path, monkeypatch) -> None:
        import smart_dl.extractors.education as edu
        from smart_dl.extractors.education import CourseLesson, CourseOutline

        calls = {"get_yt": 0, "download": 0}

        def fake_get_yt(url):
            calls["get_yt"] += 1
            # Only lesson URLs should be probed; return formats so download runs.
            if "course/" in url and "ویدیو-" in url:
                return {"formats": [{"format_id": "1"}]}
            return None

        def fake_download_yt(*a, **k):
            calls["download"] += 1
            return True

        import smart_dl.extractors.youtube as yt

        monkeypatch.setattr(yt, "get_yt_formats", fake_get_yt)
        monkeypatch.setattr(yt, "download_yt", fake_download_yt)

        outline = CourseOutline(
            platform="Maktabkhooneh",
            course_url="https://maktabkhooneh.org/course/python-mk1/",
            title="Python",
            lessons=[
                CourseLesson(
                    title="v1",
                    url="https://maktabkhooneh.org/course/python-mk1/ویدیو-مقدمه",
                    index=0,
                )
            ],
        )
        monkeypatch.setattr(edu, "parse_course_outline", lambda url, html=None: outline)

        ok = edu.download_education_course(
            "https://maktabkhooneh.org/course/python-mk1/", tmp_path
        )
        assert ok is True
        # Landing page must not call get_yt_formats for the course URL itself.
        assert calls["get_yt"] == 1  # only the lesson
        assert calls["download"] == 1

    def test_lecture_url_still_uses_yt_dlp_first(self, tmp_path, monkeypatch) -> None:
        import smart_dl.extractors.education as edu
        import smart_dl.extractors.youtube as yt

        monkeypatch.setattr(
            yt, "get_yt_formats", lambda url: {"formats": [{"format_id": "1"}]}
        )
        monkeypatch.setattr(yt, "download_yt", lambda *a, **k: True)
        ok = edu.download_education_course(
            "https://maktabkhooneh.org/course/x/ویدیو-مقدمه", tmp_path
        )
        assert ok is True


class TestMaxLessonsHelper:
    def test_resolve_max_lessons_defaults(self) -> None:
        from smart_dl.cli import resolve_education_max_lessons

        assert resolve_education_max_lessons(all_lessons=False, max_lessons=None) == 20
        assert resolve_education_max_lessons(all_lessons=True, max_lessons=None) is None
        assert resolve_education_max_lessons(all_lessons=False, max_lessons=5) == 5
        assert resolve_education_max_lessons(all_lessons=True, max_lessons=5) is None


class TestQueueDownloadItem:
    def test_best_format_does_not_open_menu(self, monkeypatch, tmp_path) -> None:
        import smart_dl.extractors.youtube as yt
        from smart_dl import cli as cli_mod

        menu_calls = {"n": 0}
        monkeypatch.setattr(
            yt,
            "download_yt",
            lambda url, folder, fmt, is_audio=False: "bestvideo" in str(fmt),
        )

        def boom(*a, **k):
            menu_calls["n"] += 1
            raise AssertionError("menu must not open")

        monkeypatch.setattr(yt, "yt_quality_menu", boom)
        monkeypatch.setattr(yt, "get_yt_formats", boom)

        ok = cli_mod.queue_download_item(
            {
                "id": 1,
                "url": "https://example.com/v",
                "format_str": "best",
                "is_audio": 0,
            },
            tmp_path,
        )
        assert ok is True
        assert menu_calls["n"] == 0
