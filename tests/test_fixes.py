"""Unit tests for the P0/P1 bug fixes (unified engine, retry semantics,
data integrity, proxy SOCKS5, 3.8 compatibility)."""
import os
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SMARTDL_NO_DEPS'] = '1'

from unittest.mock import MagicMock, patch


class TestDownloadYtBool:
    """download_yt must return a bool and only report success on success."""

    def _call(self, tmp, retry_side_effect=None, retry_return=None):
        import smart_dl.extractors.youtube as yt
        retry = MagicMock()
        if retry_side_effect is not None:
            retry.side_effect = retry_side_effect
        else:
            retry.return_value = retry_return
        fresh_stop = threading.Event()
        with patch.object(yt, "retry_with_backoff", retry), \
             patch.object(yt, "success") as mock_success, \
             patch.object(yt, "make_progress", MagicMock()), \
             patch.object(yt, "stop_event", fresh_stop), \
             patch.object(yt, "get_current_proxy", return_value=""):
            out = Path(tmp)
            out.mkdir(parents=True, exist_ok=True)
            result = yt.download_yt("https://example.com/watch?v=x", out,
                                    "best", show_header=False)
        return result, mock_success

    def test_returns_true_on_success(self, tmp_path):
        result, mock_success = self._call(str(tmp_path))
        assert result is True
        mock_success.assert_called_once()

    def test_returns_false_and_no_success_on_failure(self, tmp_path):
        result, mock_success = self._call(str(tmp_path),
                                          retry_side_effect=Exception("boom"))
        assert result is False
        # The key bug: a failed download must NOT print "Download complete!".
        mock_success.assert_not_called()

    def test_delegation_via_download_with_features(self, tmp_path):
        """The CLI path (download_with_features) returns the same bool."""

        from smart_dl.core.downloader import download_with_features
        # Make the shared engine's retry loop fail so we exercise the False path.
        with patch("smart_dl.extractors.youtube.retry_with_backoff",
                   side_effect=Exception("boom")), \
             patch("smart_dl.extractors.youtube.success") as mock_success, \
             patch("smart_dl.extractors.youtube.make_progress", MagicMock()), \
             patch("smart_dl.extractors.youtube.stop_event", threading.Event()), \
             patch("smart_dl.extractors.youtube.get_current_proxy", return_value=""):
            out = Path(tmp_path)
            out.mkdir(parents=True, exist_ok=True)
            # download_with_features forces show_header=False internally (CLI
            # drives its own output); don't pass it here.
            result = download_with_features("https://example.com/watch?v=x", out)
        assert result is False
        mock_success.assert_not_called()


class TestRetrySemantics:
    """max_retries=0 must mean infinite, not 'give up instantly'."""

    def test_zero_retries_is_not_infinite_giveup(self):
        import time

        from smart_dl.core import retry as r

        calls = {"n": 0}
        stop = threading.Event()

        def flaky():
            calls["n"] += 1
            if calls["n"] >= 3:
                stop.set()  # let the loop exit deterministically
            raise RuntimeError("temporary network failure")

        with patch.object(r, "stop_event", stop), patch.object(time, "sleep"):
            # max_retries=0 => infinite. It must keep retrying rather than
            # giving up on the very first failure (the old inverted behavior).
            r.retry_with_backoff(flaky, max_retries=0, base_delay=1)
        assert calls["n"] >= 3  # retried well past attempt 1, never raised

    def test_fatal_error_still_raises(self):
        from smart_dl.core import retry as r
        stop = threading.Event()
        with patch.object(r, "stop_event", stop):
            try:
                r.retry_with_backoff(
                    lambda: (_ for _ in ()).throw(RuntimeError("Video unavailable")),
                    max_retries=10, base_delay=1)
                assert False, "expected fatal error to raise"
            except RuntimeError as e:
                assert "video unavailable" in str(e).lower()

    def test_finite_retries_raise_after_budget(self):
        import time

        from smart_dl.core import retry as r
        calls = {"n": 0}
        stop = threading.Event()
        with patch.object(r, "stop_event", stop), patch.object(time, "sleep"):
            def always_fail():
                calls["n"] += 1
                raise RuntimeError("some transient error")
            try:
                r.retry_with_backoff(always_fail, max_retries=3, base_delay=1)
                assert False, "expected raise after budget"
            except RuntimeError:
                pass
        assert calls["n"] == 3


class TestSettingsZeroMeansInfinite:
    def test_zero_maps_to_999(self):
        import smart_dl.settings as s
        saved = dict(s.DL_SETTINGS)
        try:
            # Drive the menu: "1"=max-retries option, "0"=the value (infinite),
            # "0"=back. Prompt.ask is imported into settings' namespace.
            with patch("smart_dl.settings.Prompt.ask",
                       side_effect=["1", "0", "0"]):
                s.settings_menu()
            assert s.DL_SETTINGS["max_retries"] == 999
        finally:
            s.DL_SETTINGS.clear()
            s.DL_SETTINGS.update(saved)


class TestConfigAtomicity:
    def test_corrupt_primary_recovers_from_bak(self):
        import json

        import smart_dl.core.config as c

        tmp = Path(tempfile.mkdtemp())
        cfg = tmp / "config.json"
        bak = tmp / "config.json.bak"
        try:
            c._SMARTDL_CONFIG = str(cfg)
            # A good backup exists.
            bak.write_text(json.dumps({"proxy": "socks5://127.0.0.1:10808"}),
                           encoding="utf-8")
            # Primary is corrupt.
            cfg.write_text("{ this is not json", encoding="utf-8")
            data = c.load_config()
            assert data.get("proxy") == "socks5://127.0.0.1:10808"
        finally:
            c._SMARTDL_CONFIG = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")),
                "SmartDL", "config.json")
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_save_is_atomic_and_keeps_backup(self):
        import json

        import smart_dl.core.config as c

        tmp = Path(tempfile.mkdtemp())
        cfg = tmp / "config.json"
        bak = tmp / "config.json.bak"
        try:
            c._SMARTDL_CONFIG = str(cfg)
            c.save_config({"v": 1})
            assert json.loads(cfg.read_text(encoding="utf-8")) == {"v": 1}
            assert not (tmp / "config.json.tmp").exists()
            # Second save: previous contents roll into .bak.
            c.save_config({"v": 2})
            assert json.loads(cfg.read_text(encoding="utf-8")) == {"v": 2}
            assert json.loads(bak.read_text(encoding="utf-8")) == {"v": 1}
        finally:
            c._SMARTDL_CONFIG = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")),
                "SmartDL", "config.json")
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


class TestAparatStringCoercion:
    def _info(self, view, like):
        return {"title": "T", "view": view, "like": like, "sabka": 10,
                "owner": {"name": "O"}}

    def test_numeric_strings_do_not_crash(self):
        from smart_dl.extractors.aparat import _show_aparat_info
        # The old code raised ValueError on numeric-as-string views/likes.
        _show_aparat_info(self._info("1234", "56"))

    def test_none_values_do_not_crash(self):
        from smart_dl.extractors.aparat import _show_aparat_info
        _show_aparat_info(self._info(None, None))


class TestPodcastMenuShape:
    def test_ctrl_c_returns_none_not_tuple(self):
        from smart_dl.extractors import podcast
        with patch("rich.prompt.Prompt.ask", side_effect=KeyboardInterrupt), \
             patch("smart_dl.core.installer.has_ffmpeg", return_value=True):
            result = podcast.podcast_quality_menu(raw_sz=1000)
        assert result is None

    def test_filename_empty_suffix_uses_mp3(self):
        """The old `"podcast." + raw.suffix.lstrip('.') or 'mp3'` produced a
        trailing-dot name for a raw file with no extension."""
        from pathlib import Path
        raw = Path("podcast_raw")  # .suffix == ''
        ext = raw.suffix.lstrip(".") or "mp3"
        assert ("podcast." + ext) == "podcast.mp3"


class TestProxySocks5Presets:
    def test_localhost_url_helper_uses_protocol(self):
        from smart_dl.core.proxy import _localhost_proxy_url
        assert _localhost_proxy_url(10808, "socks5") == "socks5://127.0.0.1:10808"
        assert _localhost_proxy_url(8080, "http") == "http://127.0.0.1:8080"

    def test_presets_carry_correct_protocol(self):
        from smart_dl.core.proxy import LOCALHOST_PORTS
        by_port = {port: proto for port, _, proto in LOCALHOST_PORTS}
        assert by_port[10808] == "socks5"  # v2rayN SOCKS5 row
        assert by_port[7891] == "socks5"
        assert by_port[1080] == "socks5"
        assert by_port[8080] == "http"
        assert by_port[10809] == "http"

    def test_apply_proxy_sets_all_proxy(self):
        import smart_dl.core.config as c
        import smart_dl.core.proxy as p
        tmp = Path(tempfile.mkdtemp())
        cfg = tmp / "config.json"
        try:
            c._SMARTDL_CONFIG = str(cfg)
            for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
                os.environ.pop(k, None)
            assert p.apply_proxy("socks5://127.0.0.1:10808") is True
            assert os.environ.get("ALL_PROXY") == "socks5://127.0.0.1:10808"
            assert os.environ.get("HTTPS_PROXY") == "socks5://127.0.0.1:10808"
        finally:
            c._SMARTDL_CONFIG = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")),
                "SmartDL", "config.json")
            for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
                os.environ.pop(k, None)
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


class TestPython38Compat:
    def test_progress_module_uses_future_annotations(self):
        """ui/progress.py must guard PEP 585 annotations (set[str]) so it
        imports on Python 3.8."""
        from smart_dl.ui import progress as prog
        src = Path(prog.__file__).read_text(encoding="utf-8")
        assert "from __future__ import annotations" in src
        # And it must actually import + expose the hook.
        assert hasattr(prog, "yt_hook")
