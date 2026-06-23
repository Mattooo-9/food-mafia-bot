"""Фоновый watchdog: память, счётчик критических ошибок."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)

_critical_errors = 0


def record_critical_error() -> None:
    global _critical_errors
    _critical_errors += 1


def _memory_mb() -> float:
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:  # noqa: BLE001
        return 0.0


async def watchdog_loop() -> None:
    if not settings.watchdog_enabled:
        return
    max_mb = settings.watchdog_max_memory_mb
    max_errors = settings.watchdog_max_critical_errors
    interval = settings.watchdog_interval_seconds

    while True:
        await asyncio.sleep(interval)
        mem = _memory_mb()
        if mem > max_mb > 0:
            logger.critical("Watchdog: память %.0f MB > %s — перезапуск", mem, max_mb)
            os._exit(1)
        if _critical_errors >= max_errors > 0:
            logger.critical("Watchdog: %s критических ошибок — перезапуск", _critical_errors)
            os._exit(1)
        if mem > 0:
            logger.debug("Watchdog OK: %.0f MB, errors=%s", mem, _critical_errors)


def run_supervised() -> None:
    """Обёртка процесса: перезапуск main.py при падении."""
    import subprocess

    root = Path(__file__).resolve().parent.parent.parent
    main_py = root / "main.py"
    backoff = 3
    while True:
        logger.info("Watchdog: запуск %s", main_py)
        proc = subprocess.run([sys.executable, str(main_py)], cwd=str(root))
        code = proc.returncode
        if code == 0:
            logger.info("Watchdog: штатный выход")
            break
        logger.error("Watchdog: код %s — перезапуск через %ss", code, backoff)
        import time

        time.sleep(backoff)
        backoff = min(backoff * 2, 60)
