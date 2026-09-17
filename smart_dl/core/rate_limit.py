"""Download rate-limit helpers (roadmap R3)."""

from __future__ import annotations

import re
from typing import Optional

__all__ = ["parse_limit_rate"]

_RATE_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([KMG]?)\s*$", re.IGNORECASE)

_UNIT_BYTES = {
    "": 1,
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
}


def parse_limit_rate(value: Optional[str]) -> Optional[int]:
    """Parse a human rate limit into bytes/second for yt-dlp ``ratelimit``.

    Parameters
    ----------
    value : str or None
        Examples: ``500K``, ``2M``, ``1.5M``, ``1048576``. ``None``/empty disables.

    Returns
    -------
    int or None
        Bytes per second, or ``None`` when the limit is disabled/invalid.

    Examples
    --------
    >>> parse_limit_rate("2M")
    2097152
    >>> parse_limit_rate(None) is None
    True
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = _RATE_RE.match(text)
    if not match:
        return None
    number = float(match.group(1))
    unit = (match.group(2) or "").upper()
    if number <= 0:
        return None
    return int(number * _UNIT_BYTES[unit])
