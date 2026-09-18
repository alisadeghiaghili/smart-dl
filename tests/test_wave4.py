"""Wave 4 tests: i18n parity, aria2 RPC, local HTTP API."""

from __future__ import annotations

import json
from pathlib import Path

from smart_dl.cli import build_parser
from smart_dl.core.aria2_rpc import (
    aria2_rpc_enabled,
    get_aria2_rpc_settings,
    send_to_aria2_rpc,
)
from smart_dl.core.config import save_config, set_config_path_for_tests
from smart_dl.core.http_api import (
    api_token_ok,
    handle_api_request,
    start_api_server,
)
from smart_dl.lang import language_key_parity, set_lang, t


class TestI18nParity:
    def test_en_fa_keys_aligned(self):
        report = language_key_parity()
        assert report["missing_in_fa"] == [], report["missing_in_fa"]
        assert report["missing_in_en"] == [], report["missing_in_en"]
        assert report["en_count"] == report["fa_count"]
        assert report["en_count"] > 100

    def test_cli_keys_translate(self):
        set_lang("en")
        assert "queue" in t("cli_queue_added", n=2).lower() or "2" in t("cli_queue_added", n=2)
        set_lang("fa")
        assert t("cli_all_done") != "cli_all_done"
        set_lang("en")


class TestAria2Rpc:
    def test_settings_normalize_url(self):
        settings = get_aria2_rpc_settings({"aria2_rpc_url": "127.0.0.1:6800"})
        assert settings["url"] == "http://127.0.0.1:6800/jsonrpc"
        assert aria2_rpc_enabled({"aria2_rpc_url": ""}) is False
        assert aria2_rpc_enabled({"aria2_rpc_url": "http://127.0.0.1:6800/jsonrpc"}) is True

    def test_send_uses_injected_http_and_token(self):
        posted = []

        class Resp:
            def read(self):
                return json.dumps({"jsonrpc": "2.0", "id": 1, "result": "gid123"}).encode()

        def http(url, data=None, timeout=None):
            posted.append({"url": url, "data": json.loads(data.decode())})
            return Resp()

        result = send_to_aria2_rpc(
            ["https://example.com/a.mp4"],
            config={"aria2_rpc_url": "http://127.0.0.1:6800", "aria2_rpc_secret": "s3cret"},
            http=http,
        )
        assert result["ok"] is True
        assert result["results"] == ["gid123"]
        assert posted[0]["url"] == "http://127.0.0.1:6800/jsonrpc"
        assert posted[0]["data"]["params"][0] == "token:s3cret"
        assert posted[0]["data"]["params"][1] == ["https://example.com/a.mp4"]

    def test_send_without_config_fails_closed(self):
        result = send_to_aria2_rpc(["https://x"], config={"aria2_rpc_url": ""})
        assert result["ok"] is False
        assert "not set" in result["error"]

    def test_cli_flag(self):
        args = build_parser().parse_args(["--aria2-rpc", "https://a", "https://b"])
        assert args.aria2_rpc == ["https://a", "https://b"]


class TestHttpApi:
    def test_health(self, tmp_path: Path):
        set_config_path_for_tests(tmp_path / "c.json")
        try:
            status, payload = handle_api_request("GET", "/health")
            assert status == 200
            assert payload["ok"] is True
            assert payload["app"] == "smart-dl"
        finally:
            set_config_path_for_tests(None)

    def test_token_enforced_when_configured(self, tmp_path: Path):
        set_config_path_for_tests(tmp_path / "c.json")
        try:
            save_config({"api_token": "topsecret"})
            status, payload = handle_api_request("GET", "/health")
            assert status == 401
            status, payload = handle_api_request(
                "GET", "/health", headers={"Authorization": "Bearer topsecret"}
            )
            assert status == 200
        finally:
            set_config_path_for_tests(None)

    def test_queue_post_and_get(self, tmp_path: Path):
        from smart_dl.core.queue import set_queue_db_path_for_tests

        set_config_path_for_tests(tmp_path / "c.json")
        set_queue_db_path_for_tests(tmp_path / "q.db")
        try:
            body = json.dumps({"urls": ["https://example.com/api1"]}).encode()
            status, payload = handle_api_request("POST", "/queue", body=body)
            assert status == 200 and payload["added"] == 1
            status, payload = handle_api_request("GET", "/queue")
            assert status == 200
            assert any("api1" in item["url"] for item in payload["items"])
            status, payload = handle_api_request("GET", "/history?limit=5")
            assert status == 200 and payload["ok"] is True
        finally:
            set_config_path_for_tests(None)
            set_queue_db_path_for_tests(None)

    def test_rejects_non_localhost_bind(self):
        try:
            start_api_server(host="0.0.0.0", port=18765)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "localhost" in str(exc).lower()

    def test_live_http_roundtrip(self, tmp_path: Path):
        import urllib.error
        import urllib.request

        set_config_path_for_tests(tmp_path / "c.json")
        save_config({"api_token": "livetoken"})
        # Bypass system proxy (e.g. socks5) for loopback API tests.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            server = start_api_server(host="127.0.0.1", port=18766, background=True)
            try:
                req = urllib.request.Request("http://127.0.0.1:18766/health")
                try:
                    opener.open(req, timeout=3)
                    raise AssertionError("expected 401")
                except urllib.error.HTTPError as exc:
                    assert exc.code == 401
                req2 = urllib.request.Request(
                    "http://127.0.0.1:18766/health",
                    headers={"Authorization": "Bearer livetoken"},
                )
                with opener.open(req2, timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                assert data["ok"] is True
            finally:
                server.shutdown()
        finally:
            set_config_path_for_tests(None)

    def test_cli_flags(self):
        args = build_parser().parse_args(["--api", "--api-port", "9001"])
        assert args.api is True
        assert args.api_port == 9001

    def test_api_token_ok(self):
        assert api_token_ok("x", config={}) is True
        assert api_token_ok("x", config={"api_token": "y"}) is False
        assert api_token_ok("y", config={"api_token": "y"}) is True
