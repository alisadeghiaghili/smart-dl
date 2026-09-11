"""Tests for SOCKS5 proxy URL generation with DNS-through-proxy."""

import os
from unittest.mock import patch

from smart_dl.core.proxy import _localhost_url, _peek_registry_proxy, apply_proxy


def test_localhost_socks_port_uses_socks5h():
    """Test that SOCKS5 ports map to socks5h:// for remote DNS resolution."""
    assert _localhost_url(10808) == "socks5h://127.0.0.1:10808"
    assert _localhost_url(7891) == "socks5h://127.0.0.1:7891"
    assert _localhost_url(2080) == "socks5h://127.0.0.1:2080"


def test_localhost_http_port_uses_http():
    """Test that HTTP ports map to http://."""
    assert _localhost_url(7890) == "http://127.0.0.1:7890"
    assert _localhost_url(10809) == "http://127.0.0.1:10809"
    assert _localhost_url(8080) == "http://127.0.0.1:8080"


def test_apply_proxy_validates_and_sets():
    """Test setting a valid proxy URL."""
    with patch("smart_dl.core.proxy.save_config"), patch("smart_dl.core.proxy.load_config", return_value={}):
        assert apply_proxy("socks5h://127.0.0.1:10808") is True
        assert os.environ.get("HTTP_PROXY") == "socks5h://127.0.0.1:10808"
        assert os.environ.get("HTTPS_PROXY") == "socks5h://127.0.0.1:10808"


def test_apply_proxy_rejects_invalid():
    """Test rejecting invalid proxy strings."""
    assert apply_proxy("invalid-proxy") is False


def test_apply_proxy_socks5_suggests_socks5h():
    """Test that setting socks5:// emits a tip recommending socks5h://."""
    with patch("smart_dl.core.proxy.save_config"), \
         patch("smart_dl.core.proxy.load_config", return_value={}), \
         patch("smart_dl.core.proxy.info") as mock_info:
        assert apply_proxy("socks5://127.0.0.1:10808") is True
        assert any("socks5h://" in str(call) for call in mock_info.call_args_list)


def test_registry_socks_port_uses_socks5h():
    """Test that registry proxy detection produces socks5h:// for SOCKS ports."""
    from unittest.mock import MagicMock
    mock_wr = MagicMock()
    mock_wr.OpenKey.return_value = MagicMock()
    mock_wr.QueryValueEx.side_effect = [
        (1, 4),  # ProxyEnable = 1
        ("127.0.0.1:10808", 1),  # ProxyServer
    ]
    with patch.dict("sys.modules", {"winreg": mock_wr}):
        assert _peek_registry_proxy() == "socks5h://127.0.0.1:10808"

    mock_wr.QueryValueEx.side_effect = [
        (1, 4),  # ProxyEnable = 1
        ("socks=127.0.0.1:10808;http=127.0.0.1:10809", 1),  # ProxyServer
    ]
    with patch.dict("sys.modules", {"winreg": mock_wr}):
        assert _peek_registry_proxy() == "socks5h://127.0.0.1:10808"

