"""Unit tests for smart_dl.core.parallel — per-thread direct-to-disk downloads."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from threading import Event
from unittest.mock import MagicMock, patch

import requests


def _fake_response(body: bytes):
    """Build a context-manager ``requests.Response`` whose ``.raw`` is a BytesIO."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 200
    resp.raw = MagicMock()
    it = iter([body[i : i + 4096] for i in range(0, len(body), 4096)] + [b""])

    def fake_read(amt=-1):
        try:
            return next(it)
        except StopIteration:
            return b""

    resp.raw.read = fake_read
    resp.raise_for_status = MagicMock()
    resp.__enter__ = lambda self: resp
    resp.__exit__ = lambda self, *a: False
    return resp


class TestParallelDownloads:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_items_returns_empty_list(self):
        from smart_dl.core.parallel import parallel_downloads

        assert parallel_downloads([]) == []

    def test_single_item_downloads_to_disk(self):
        from smart_dl.core.parallel import parallel_downloads

        body = b"hello world" * 1000
        resp = _fake_response(body)
        with patch("requests.Session") as MockSession:
            sess = MockSession.return_value
            sess.get.return_value = resp
            sess.proxies = {}
            dest = self.tmp / "out.bin"
            results = parallel_downloads(
                [("http://example.com/x", dest)], max_workers=1
            )
        assert results[0] == dest
        assert dest.read_bytes() == body

    def test_multiple_items_download_in_parallel(self):
        from smart_dl.core.parallel import parallel_downloads

        items = []
        bodies = {}
        for i in range(3):
            dest = self.tmp / f"f{i}.bin"
            body = (f"payload{i}!" * 500).encode()
            bodies[dest] = body
            items.append((f"http://example.com/{i}", dest))

        with patch("requests.Session") as MockSession:

            def session_factory():
                s = MagicMock()
                s.proxies = {}

                def get(url, stream=True, timeout=30):
                    idx = int(url.rsplit("/", 1)[-1])
                    dest = self.tmp / f"f{idx}.bin"
                    return _fake_response(bodies[dest])

                s.get.side_effect = get
                return s

            MockSession.side_effect = session_factory
            results = parallel_downloads(items, max_workers=3)

        assert all(r is not None for r in results)
        for dest, body in bodies.items():
            assert dest.read_bytes() == body

    def test_cancel_event_aborts_remaining(self):
        from smart_dl.core.parallel import parallel_downloads

        cancel = Event()
        cancel.set()
        dest = self.tmp / "cancelled.bin"
        results = parallel_downloads(
            [("http://example.com/x", dest)], max_workers=1, cancel=cancel
        )
        assert results[0] is None
        assert not dest.exists()

    def test_proxy_passed_to_session(self):
        from smart_dl.core.parallel import parallel_downloads

        body = b"x" * 100
        resp = _fake_response(body)
        with patch("requests.Session") as MockSession:
            sess = MockSession.return_value
            sess.get.return_value = resp
            dest = self.tmp / "p.bin"
            parallel_downloads(
                [("http://example.com/x", dest)],
                proxy="socks5://127.0.0.1:1080",
                max_workers=1,
            )
            assert sess.proxies == {
                "http": "socks5://127.0.0.1:1080",
                "https": "socks5://127.0.0.1:1080",
            }


class TestParallelDetailedResults:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_failure_records_error(self):
        from smart_dl.core.parallel import parallel_download_results

        results = parallel_download_results(
            [("http://127.0.0.1:9/none", self.tmp / "x.bin")],
            max_workers=1,
        )
        assert results[0].ok is False
        assert results[0]["error"]

    def test_no_partial_file_left_on_failure(self):
        from smart_dl.core.parallel import parallel_download_results

        dest = self.tmp / "fail.bin"
        results = parallel_download_results(
            [("http://127.0.0.1:9/none", dest)], max_workers=1
        )
        assert results[0].ok is False
        assert not dest.exists()
        assert not dest.with_name(dest.name + ".part").exists()
