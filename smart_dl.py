"""Interactive bootstrap — ``python smart_dl.py``."""

from __future__ import annotations

import sys

from smart_dl.__main__ import main
from smart_dl import VERSION

if __name__ == "__main__":
    sys.exit(main())

__all__ = ["VERSION", "main"]
