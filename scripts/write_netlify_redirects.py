#!/usr/bin/env python3
"""Write Netlify _redirects to proxy API/uploads/webhook to the active backend."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "frontend" / "dist"


def main() -> None:
    backend = os.environ.get("BACKEND_URL", "").strip().rstrip("/")
    if not backend:
        raise SystemExit("BACKEND_URL is required")

    if not DIST.exists():
        raise SystemExit(f"{DIST} not found — run frontend build first")

    lines = [
        f"/api/*  {backend}/api/:splat  200",
        f"/uploads/*  {backend}/uploads/:splat  200",
        f"/tg/webhook  {backend}/tg/webhook  200",
        "/*  /index.html  200",
    ]
    redirects = DIST / "_redirects"
    redirects.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {redirects} -> {backend}")


if __name__ == "__main__":
    main()
