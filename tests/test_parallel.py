"""Unit tests for smart_dl.core.parallel — per-thread direct-to-disk downloads."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SMARTDL_NO_DEPS'] = '1'

from threading import Event
from unittest.mock import MagicMock, patch

import requests


class TestParallelDownloads:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fake_response(self, body: bytes):
        """Build a context-manager `requests.Response` whose .raw is a BytesIO."""
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        resp.raw = MagicMock()
        # copyfileobj reads from resp.raw in chunks. Patch read to drain `body`.
        it = iter([body[i:i + 4096] for i in range(0, len(body), 4096)] + [b""])

        def fake_read(amt=-1):
            try:
                return next(it)
            except StopIteration:
                return b""
        resp.raw.read = fake_read
        resp.raise_for_status = MagicMock()
        # Make the response usable as a context manager
        resp.__enter__ = lambda self: resp
        resp.__exit__ = lambda self, *a: False
        return resp

    def test_empty_items_returns_empty_list(self):
        from smart_dl.core.parallel import parallel_downloads
        assert parallel_downloads([]) == []

    def test_single_item_downloads_to_disk(self):
        from smart_dl.core.parallel import parallel_downloads
        body = b"hello world" * 1000
        resp = self._fake_response(body)
        with patch("requests.Session") as MockSession:
            sess = MockSession.return_value
            sess.get.return_value = resp
            sess.proxies = {}
            dest = self.tmp / "out.bin"
            results = parallel_downloads([("http://example.com/x", dest)], max_workers=1)
        assert results[0] == dest
        assert dest.read_bytes() == body

    def test_multiple_items_download_in_parallel(self):
        from smart_dl.core.parallel import parallel_downloads
        items = []
        responses = {}
        for i in range(5):
            body = f"file-{i}-payload".encode() * 100
            dest = self.tmp / f"f{i}.bin"
            items.append((f"http://example.com/{i}", dest))
            responses[f"http://example.com/{i}"] = self._fake_response(body)

        with patch("requests.Session") as MockSession:
            sess = MockSession.return_value
            sess.get.side_effect = lambda url, **kw: responses[url]
            sess.proxies = {}
            results = parallel_downloads(items, max_workers=3)
        for i, dest in enumerate([it[1] for it in items]):
            assert results[i] == dest
            assert dest.read_bytes() == f"file-{i}-payload".encode() * 100

    def test_cancel_event_aborts_remaining(self):
        from smart_dl.core.parallel import parallel_downloads
        cancel = Event()
        cancel.set()  # pre-cancelled
        items = [("http://example.com/0", self.tmp / "a.bin")]
        with patch("requests.Session"):
            results = parallel_downloads(items, cancel=cancel)
        # Should return None without ever calling requests
        assert results[0] is None

    def test_proxy_passed_to_session(self):
        from smart_dl.core.parallel import parallel_downloads
        resp = self._fake_response(b"x" * 100)
        with patch("requests.Session") as MockSession:
            sess = MockSession.return_value
            sess.get.return_value = resp
            sess.proxies = {}
            parallel_downloads(
                [("http://example.com/x", self.tmp / "out.bin")],
                proxy="socks5://127.0.0.1:10808",
            )
            # Session was constructed and proxies set
            assert sess.proxies == {"http": "socks5://127.0.0.1:10808",
                                    "https": "socks5://127.0.0.1:10808"}
