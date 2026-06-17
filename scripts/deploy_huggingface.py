#!/usr/bin/env python3
"""Deploy Docker Space to Hugging Face (free, no card). Needs HF_TOKEN + HF_SPACE."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    space_id = os.environ.get("HF_SPACE", "Mattooo-9/food-mafia-bot")
    if not token:
        print("HF_TOKEN not set — skip Hugging Face deploy", file=sys.stderr)
        return

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

    # HF Space README with Docker metadata
    readme_hf = ROOT / "README_HF.md"
    readme = ROOT / "README.md"
    backup: str | None = None
    if readme_hf.exists():
        if readme.exists():
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
        "terminals",
        "__pycache__",
        "*.pyc",
    ]

    try:
        upload_folder(
            folder_path=str(ROOT),
            repo_id=space_id,
            repo_type="space",
            commit_message="Deploy from GitHub Actions",
            ignore_patterns=ignore,
        )
        print(f"Hugging Face Space deployed: https://huggingface.co/spaces/{space_id}")
    finally:
        if backup is not None:
            readme.write_text(backup, encoding="utf-8")


if __name__ == "__main__":
    main()
