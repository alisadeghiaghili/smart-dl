"""Unit tests for smart_dl.core.proxy — env/registry parse + validation.

Run with: pytest tests/test_proxy.py -v
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SMARTDL_NO_DEPS'] = '1'

from unittest.mock import patch


class TestPeekEnvProxy:
    """env var lookup — no side effects."""

    def setup_method(self):
        for k in (
            "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy",
            "ALL_PROXY", "all_proxy",
            "SOCKS5_PROXY", "socks5_proxy",
            "SOCKS_PROXY", "socks_proxy",
            "SOCKS4_PROXY", "socks4_proxy",
        ):
            os.environ.pop(k, None)

    def teardown_method(self):
        for k in (
            "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy",
            "ALL_PROXY", "all_proxy",
            "SOCKS5_PROXY", "socks5_proxy",
            "SOCKS_PROXY", "socks_proxy",
            "SOCKS4_PROXY", "socks4_proxy",
        ):
            os.environ.pop(k, None)

    def test_returns_empty_when_no_env_vars_set(self):
        from smart_dl.core.proxy import _peek_env_proxy
        assert _peek_env_proxy() == ""

    def test_reads_uppercase_https_proxy(self):
        from smart_dl.core.proxy import _peek_env_proxy
        os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8080"
        assert _peek_env_proxy() == "http://127.0.0.1:8080"

    def test_reads_lowercase_http_proxy(self):
        from smart_dl.core.proxy import _peek_env_proxy
        os.environ["http_proxy"] = "http://127.0.0.1:8080"
        assert _peek_env_proxy() == "http://127.0.0.1:8080"

    def test_reads_socks5_proxy(self):
        from smart_dl.core.proxy import _peek_env_proxy
        os.environ["SOCKS5_PROXY"] = "socks5://127.0.0.1:10808"
        assert _peek_env_proxy() == "socks5://127.0.0.1:10808"

    def test_reads_all_proxy(self):
        from smart_dl.core.proxy import _peek_env_proxy
        os.environ["ALL_PROXY"] = "socks5://127.0.0.1:10808"
        assert _peek_env_proxy() == "socks5://127.0.0.1:10808"

    def test_priority_https_then_http(self):
        from smart_dl.core.proxy import _peek_env_proxy
        os.environ["HTTP_PROXY"] = "http://127.0.0.1:8080"
        os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8443"
        # HTTPS_PROXY should win
        assert _peek_env_proxy() == "http://127.0.0.1:8443"


class TestPeekRegistryProxy:
    """Windows registry parse — three input shapes."""

    def test_disabled_returns_empty(self):
        from smart_dl.core.proxy import _peek_registry_proxy
        with patch("winreg.OpenKey"), \
             patch("winreg.QueryValueEx", side_effect=[(0, ""), ("", "")]):
            assert _peek_registry_proxy() == ""

    def test_simple_host_port_assumes_http(self):
        from smart_dl.core.proxy import _peek_registry_proxy
        with patch("winreg.OpenKey"), \
             patch("winreg.QueryValueEx", side_effect=[(1, ""), ("127.0.0.1:8080", "")]):
            assert _peek_registry_proxy() == "http://127.0.0.1:8080"

    def test_simple_host_port_with_socks_port_gets_socks5(self):
        """If the simple form has a known SOCKS port, prefix socks5://."""
        from smart_dl.core.proxy import _peek_registry_proxy
        with patch("winreg.OpenKey"), \
             patch("winreg.QueryValueEx", side_effect=[(1, ""), ("127.0.0.1:10808", "")]):
            assert _peek_registry_proxy() == "socks5://127.0.0.1:10808"

    def test_https_key_wins_in_protocol_specific(self):
        from smart_dl.core.proxy import _peek_registry_proxy
        with patch("winreg.OpenKey"), \
             patch("winreg.QueryValueEx", side_effect=[(1, ""), ("http=127.0.0.1:8080;https=127.0.0.1:8443", "")]):
            assert _peek_registry_proxy() == "http://127.0.0.1:8443"

    def test_socks_key_wins_over_http_https(self):
        """v2rayN/Hiddify/Nekoray default — socks= must take priority."""
        from smart_dl.core.proxy import _peek_registry_proxy
        with patch("winreg.OpenKey"), \
             patch("winreg.QueryValueEx", side_effect=[(1, ""), (
                "socks=127.0.0.1:10808;http=127.0.0.1:8080;https=127.0.0.1:8443", "")]):
            assert _peek_registry_proxy() == "socks5://127.0.0.1:10808"

    def test_socks_only_with_no_http_returns_socks5(self):
        """The exact bug case from the report: only socks= set, no http/https.
        Old code returned 'http://socks=127.0.0.1:10808' (broken).
        New code returns 'socks5://127.0.0.1:10808'."""
        from smart_dl.core.proxy import _peek_registry_proxy
        with patch("winreg.OpenKey"), \
             patch("winreg.QueryValueEx", side_effect=[(1, ""), ("socks=127.0.0.1:10808", "")]):
            assert _peek_registry_proxy() == "socks5://127.0.0.1:10808"

    def test_handles_missing_registry_key(self):
        from smart_dl.core.proxy import _peek_registry_proxy
        with patch("winreg.OpenKey", side_effect=FileNotFoundError()):
            assert _peek_registry_proxy() == ""


class TestApplyProxyValidation:
    """apply_proxy must reject malformed URLs so bad registry parse can't poison config."""

    def setup_method(self):
        import smart_dl.core.config as config_mod
        self._orig = config_mod._SMARTDL_CONFIG
        tmp = Path(tempfile_get_tmpdir()) / "test_proxy_config.json"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        config_mod._SMARTDL_CONFIG = str(tmp)
        # Clear all proxy env vars so each test starts clean
        for k in (
            "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
            "ALL_PROXY", "all_proxy",
            "SOCKS5_PROXY", "socks5_proxy",
            "SOCKS_PROXY", "socks_proxy",
            "SOCKS4_PROXY", "socks4_proxy",
        ):
            os.environ.pop(k, None)

    def teardown_method(self):
        import smart_dl.core.config as config_mod
        config_mod._SMARTDL_CONFIG = self._orig
        for k in (
            "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
            "ALL_PROXY", "all_proxy",
            "SOCKS5_PROXY", "socks5_proxy",
            "SOCKS_PROXY", "socks_proxy",
            "SOCKS4_PROXY", "socks4_proxy",
        ):
            os.environ.pop(k, None)
        try:
            Path(self._orig).unlink(missing_ok=True)
        except Exception:
            pass

    def test_valid_http_proxy_accepted(self):
        from smart_dl.core.proxy import apply_proxy
        assert apply_proxy("http://127.0.0.1:8080") is True
        assert os.environ.get("HTTP_PROXY") == "http://127.0.0.1:8080"

    def test_valid_socks5_proxy_accepted(self):
        from smart_dl.core.proxy import apply_proxy
        assert apply_proxy("socks5://127.0.0.1:10808") is True
        assert os.environ.get("HTTPS_PROXY") == "socks5://127.0.0.1:10808"

    def test_malformed_url_rejected(self):
        from smart_dl.core.proxy import apply_proxy
        assert apply_proxy("socks=127.0.0.1:10808;http=...") is False
        assert os.environ.get("HTTP_PROXY", "") == ""

    def test_empty_string_rejected(self):
        from smart_dl.core.proxy import apply_proxy
        assert apply_proxy("") is False
        assert apply_proxy("   ") is False

    def test_url_without_port_rejected(self):
        from smart_dl.core.proxy import apply_proxy
        assert apply_proxy("http://127.0.0.1") is False


class TestReadOnlyPeek:
    """peek_current_proxy must not mutate env or config."""

    def test_peek_does_not_set_env_vars(self):
        from smart_dl.core.proxy import peek_current_proxy
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        # Set a config value, call peek — env vars should not be touched
        import smart_dl.core.config as config_mod
        orig = config_mod._SMARTDL_CONFIG
        tmp = Path(tempfile_get_tmpdir()) / "test_peek_config.json"
        config_mod._SMARTDL_CONFIG = str(tmp)
        try:
            from smart_dl.core.proxy import apply_proxy
            apply_proxy("http://127.0.0.1:8080")
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
            result = peek_current_proxy()
            assert result == "http://127.0.0.1:8080"
            # Critical: peek did not re-populate env vars
            assert "HTTP_PROXY" not in os.environ
            assert "HTTPS_PROXY" not in os.environ
        finally:
            config_mod._SMARTDL_CONFIG = orig
            try:
                Path(tmp).unlink(missing_ok=True)
            except Exception:
                pass


def tempfile_get_tmpdir() -> str:
    import tempfile
    return tempfile.gettempdir()
