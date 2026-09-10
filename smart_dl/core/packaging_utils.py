"""Helpers for Windows portable packaging (checksums + zip name)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, List, Tuple

__all__ = [
    "sha256_file",
    "write_checksums",
    "windows_artifact_name",
]


def windows_artifact_name(version: str, *, platform_tag: str = "win-x64") -> str:
    """Return the release artifact base name for a version.

    Parameters
    ----------
    version : str
        Package version (e.g. ``3.4.0``).
    platform_tag : str, optional
        Platform tag (default ``win-x64``).

    Returns
    -------
    str
        ``SmartDL-v{version}-{platform_tag}`` without extension.
    """
    clean = version.lstrip("v")
    return f"SmartDL-v{clean}-{platform_tag}"


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Compute the SHA-256 hex digest of a file.

    Parameters
    ----------
    path : pathlib.Path
        File to hash.
    chunk_size : int, optional
        Read buffer size.

    Returns
    -------
    str
        Lowercase hex digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(paths: Iterable[Path], output: Path) -> List[Tuple[str, str]]:
    """Write a ``SHA256SUMS``-style file (``<hash>  <filename>``).

    Parameters
    ----------
    paths : Iterable[pathlib.Path]
        Files to hash.
    output : pathlib.Path
        Destination text file.

    Returns
    -------
    list of (str, str)
        Pairs of (hash, filename) that were written.
    """
    lines: List[Tuple[str, str]] = []
    for path in paths:
        if not path.is_file():
            continue
        digest = sha256_file(path)
        lines.append((digest, path.name))
    # Always LF so checksum files match POSIX tools and GitHub releases.
    body = "".join(f"{digest}  {name}\n" for digest, name in lines)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return lines
