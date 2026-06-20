#!/usr/bin/env python3
"""One-command free deploy: build frontend → Hugging Face → sync Telegram."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd or ROOT)


def main() -> None:
    load_dotenv()
    if not os.environ.get("BOT_TOKEN"):
        raise SystemExit("BOT_TOKEN missing — add to .env")

    frontend = ROOT / "frontend"
    if (frontend / "package.json").exists():
        run(["npm", "ci"], cwd=frontend)
        run(["npm", "run", "build"], cwd=frontend)

    run([sys.executable, str(ROOT / "scripts" / "deploy_huggingface.py")])


if __name__ == "__main__":
    main()
