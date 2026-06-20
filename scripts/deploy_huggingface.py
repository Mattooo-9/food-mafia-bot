#!/usr/bin/env python3
"""Deploy to Hugging Face Space (free, no card) + sync Telegram bot."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def hf_space_public_url(space_id: str) -> str:
    owner, name = space_id.split("/", 1)
    return f"https://{owner.lower()}-{name.lower().replace('_', '-')}.hf.space"


def wait_health(url: str, attempts: int = 30, interval: int = 20) -> bool:
    import json
    import urllib.error
    import urllib.request

    health = url.rstrip("/") + "/health"
    for i in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(health, timeout=30) as resp:
                if resp.status == 200 and json.loads(resp.read()).get("status") == "ok":
                    print(f"Health OK: {health}")
                    return True
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            pass
        print(f"Waiting for {health} ({i}/{attempts})...", file=sys.stderr)
        time.sleep(interval)
    return False


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    space_id = os.environ.get("HF_SPACE", "Mattooo-9/food-mafia-bot")
    if not token:
        raise SystemExit(
            "HF_TOKEN not set.\n"
            "Create token: https://huggingface.co/settings/tokens (Write access)\n"
            "Then: set HF_TOKEN=hf_...  (PowerShell)"
        )

    try:
        from huggingface_hub import HfApi, upload_folder
    except ImportError:
        raise SystemExit("pip install huggingface_hub") from None

    api = HfApi(token=token)
    api.create_repo(
        repo_id=space_id,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
    )

    public_url = hf_space_public_url(space_id)
    print(f"Space URL: {public_url}")

    # HF Space runtime secrets (Settings → Repository secrets on HF UI)
    secret_keys = {
        "BOT_TOKEN": os.environ.get("BOT_TOKEN", ""),
        "ADMIN_ID": os.environ.get("ADMIN_ID", "0"),
        "USE_WEBHOOK": "1",
        "WEBAPP_URL": public_url,
        "WEBHOOK_SECRET": os.environ.get("WEBHOOK_SECRET", ""),
        "LOG_LEVEL": "INFO",
        "KEEP_ALIVE_INTERVAL_MINUTES": "0",
    }
    for key, value in secret_keys.items():
        if not value and key in ("BOT_TOKEN",):
            raise SystemExit(f"{key} is required")
        if value:
            try:
                api.add_space_secret(repo_id=space_id, key=key, value=value)
                print(f"Secret set: {key}")
            except Exception as exc:  # noqa: BLE001
                print(f"Warning: could not set secret {key}: {exc}", file=sys.stderr)

    readme_hf = ROOT / "README_HF.md"
    readme = ROOT / "README.md"
    backup: str | None = None
    if readme_hf.exists():
        backup = readme.read_text(encoding="utf-8")
        shutil.copy(readme_hf, readme)

    ignore = [
        ".git",
        ".github",
        ".venv",
        "node_modules",
        "frontend/node_modules",
        "database/*.db",
        "uploads/*",
        ".env",
        ".cursor",
        "__pycache__",
        "*.pyc",
    ]

    try:
        print("Uploading to Hugging Face Space...")
        upload_folder(
            folder_path=str(ROOT),
            repo_id=space_id,
            repo_type="space",
            commit_message="Deploy Еда Рядом",
            ignore_patterns=ignore,
        )
        print(f"Uploaded: https://huggingface.co/spaces/{space_id}")
    finally:
        if backup is not None:
            readme.write_text(backup, encoding="utf-8")

    print("Waiting for Space build (3–8 min)...")
    if wait_health(public_url, attempts=24, interval=20):
        os.environ["MINI_APP_URL"] = public_url
        os.environ["WEBHOOK_URL"] = public_url
        os.environ["SERVICE_URL"] = public_url
        os.environ["USE_WEBHOOK"] = "1"
        sync = ROOT / "scripts" / "sync_telegram.py"
        subprocess.run([sys.executable, str(sync)], check=True, cwd=str(ROOT))
        print(f"\nReady! Mini App: {public_url}")
        print("Open bot in Telegram → кнопка «Еда Рядом»")
    else:
        print(
            f"\nSpace is building. When ready, run:\n"
            f"  set SERVICE_URL={public_url}\n"
            f"  python scripts/sync_telegram.py",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
