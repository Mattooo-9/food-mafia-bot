#!/usr/bin/env python3
"""Alias for sync_telegram.py (backward compatible)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_telegram import main  # noqa: E402

if __name__ == "__main__":
    main()
