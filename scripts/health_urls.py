#!/usr/bin/env python3
"""Pick the first healthy public URL from a comma-separated list."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def check_health(base_url: str, timeout: float = 15.0) -> bool:
    url = base_url.rstrip("/") + "/health"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            body = resp.read().decode()
            data = json.loads(body) if body else {}
            return data.get("status") == "ok"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False


def main() -> None:
    raw = os.environ.get("BACKEND_URLS") or os.environ.get("SERVICE_URLS") or ""
    urls = [u.strip().rstrip("/") for u in raw.split(",") if u.strip()]
    if not urls:
        raise SystemExit("BACKEND_URLS or SERVICE_URLS is empty")

    wait_seconds = int(os.environ.get("HEALTH_WAIT_SECONDS", "0"))
    attempts = max(1, int(os.environ.get("HEALTH_ATTEMPTS", "1")))
    interval = int(os.environ.get("HEALTH_INTERVAL_SECONDS", "20"))

    import time

    for attempt in range(1, attempts + 1):
        for url in urls:
            if check_health(url):
                print(url)
                return
        if attempt < attempts:
            print(f"attempt {attempt}/{attempts}: no healthy URL, waiting {interval}s...", file=sys.stderr)
            time.sleep(interval)

    if wait_seconds > 0:
        time.sleep(wait_seconds)
        for url in urls:
            if check_health(url):
                print(url)
                return

    raise SystemExit(f"No healthy URL among: {', '.join(urls)}")


if __name__ == "__main__":
    main()
