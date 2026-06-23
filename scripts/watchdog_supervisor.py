#!/usr/bin/env python3
"""Production supervisor: перезапуск main.py при падении."""
from backend.cluster.watchdog import run_supervised

if __name__ == "__main__":
    run_supervised()
