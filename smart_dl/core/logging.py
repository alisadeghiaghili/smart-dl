"""Logging system — file and console logging."""
from __future__ import annotations
import logging
import sys
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None


def setup_logging(log_file: Optional[str] = None, verbose: bool = False) -> logging.Logger:
    """Set up logging to file and/or console."""
    global _logger

    if _logger is not None:
        return _logger

    _logger = logging.getLogger("smartdl")
    _logger.setLevel(logging.DEBUG)

    # Console handler (WARNING+ by default, INFO if verbose)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO if verbose else logging.WARNING)
    console_fmt = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_fmt)
    _logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        file_handler.setFormatter(file_fmt)
        _logger.addHandler(file_handler)

    return _logger


def get_logger() -> logging.Logger:
    """Get the SmartDL logger."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def log_download_start(url: str, title: str = "") -> None:
    """Log a download start event."""
    get_logger().info(f"Download started: {title or url}")


def log_download_complete(url: str, path: str, size: int = 0) -> None:
    """Log a download complete event."""
    get_logger().info(f"Download complete: {path} ({size} bytes)")


def log_download_error(url: str, error: str) -> None:
    """Log a download error event."""
    get_logger().error(f"Download failed: {url} - {error}")


def log_proxy_change(old: str, new: str) -> None:
    """Log a proxy change."""
    get_logger().info(f"Proxy changed: {old} -> {new}")
