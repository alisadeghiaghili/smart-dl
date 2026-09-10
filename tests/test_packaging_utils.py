"""Unit tests for Windows packaging helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.core.packaging_utils import (  # noqa: E402
    sha256_file,
    windows_artifact_name,
    write_checksums,
)


class TestArtifactName:
    def test_strips_v_prefix(self) -> None:
        assert windows_artifact_name("v3.4.0") == "SmartDL-v3.4.0-win-x64"
        assert windows_artifact_name("3.4.0") == "SmartDL-v3.4.0-win-x64"

    def test_custom_platform(self) -> None:
        assert windows_artifact_name("3.4.0", platform_tag="win-arm64").endswith("win-arm64")


class TestChecksums:
    def test_sha256_known_value(self, tmp_path: Path) -> None:
        sample = tmp_path / "hello.txt"
        sample.write_bytes(b"hello")
        # echo -n hello | sha256sum
        assert sha256_file(sample) == (
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        )

    def test_write_checksums_file(self, tmp_path: Path) -> None:
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"a")
        b.write_bytes(b"b")
        out = tmp_path / "SHA256SUMS"
        pairs = write_checksums([a, b, tmp_path / "missing.bin"], out)
        assert len(pairs) == 2
        text = out.read_text(encoding="utf-8")
        assert "a.bin" in text
        assert "b.bin" in text
        assert len(text.splitlines()) == 2
