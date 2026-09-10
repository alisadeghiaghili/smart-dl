"""Unit tests for Faradars Next.js helpers."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.faradars_next import (  # noqa: E402
    extract_next_build_id,
    title_from_next_json,
)


class TestBuildId:
    def test_extract(self) -> None:
        html = '{"buildId":"abc123XYZ","page":"/x"}'
        assert extract_next_build_id(html) == "abc123XYZ"

    def test_missing(self) -> None:
        assert extract_next_build_id("<html></html>") == ""


class TestTitleFromJson:
    def test_page_props_title(self) -> None:
        data = {"pageProps": {"title": "آموزش پایتون"}}
        assert title_from_next_json(data) == "آموزش پایتون"

    def test_app_fallback(self) -> None:
        data = {
            "pageProps": {
                "appFallback": {
                    "{\"url\":\"/x\"}": {"data": {"title": "دوره متلب"}}
                }
            }
        }
        assert title_from_next_json(data) == "دوره متلب"

    def test_empty(self) -> None:
        assert title_from_next_json(None) == ""
