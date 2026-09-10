"""Unit tests for CLI exit-code helpers and Faradars path extraction."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"


class TestCountFailure:
    def test_true_is_not_failure(self) -> None:
        from smart_dl.cli import count_failure

        assert count_failure(True) == 0
        assert count_failure(False) == 1
        assert count_failure(None) == 1


class TestFaradarsPaths:
    def test_extract_course_paths(self) -> None:
        from smart_dl.extractors.education import extract_faradars_course_paths

        html = """
        <a href="/how-to-learn/python-programming">Python</a>
        <a href="/fv1234-matlab">Matlab</a>
        <a href="/courses/data-science">DS</a>
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{"title":"پایتون"}}}
        </script>
        """
        paths = extract_faradars_course_paths(html)
        assert "/how-to-learn/python-programming" in paths
        assert "/fv1234-matlab" in paths
        assert "/courses/data-science" in paths

    def test_dedupes(self) -> None:
        from smart_dl.extractors.education import extract_faradars_course_paths

        html = '<a href="/fv1">x</a><a href="/fv1">y</a>'
        assert extract_faradars_course_paths(html) == ["/fv1"]
