#!/usr/bin/env python3
"""Production supervisor: перезапуск main.py при падении."""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.cluster.watchdog import run_supervised

if __name__ == "__main__":
    run_supervised()
