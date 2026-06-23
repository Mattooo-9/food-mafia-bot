#!/usr/bin/env python3
"""
Деплой Active-Passive кластера: Koyeb (primary) + Vercel (standby).

Требуется:
  - KOYEB_TOKEN (или koyeb auth login)
  - VERCEL_TOKEN (или vercel login)
  - BOT_TOKEN, DATABASE_URL, REDIS_URL в окружении или .env

Запуск:
  python scripts/deploy_cluster.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_ENV = ("BOT_TOKEN", "DATABASE_URL", "REDIS_URL")


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"'))


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd or ROOT, check=check)


def check_health(url: str) -> bool:
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return resp.status == 200 and data.get("status") == "ok"
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return False


def deploy_vercel() -> str:
    if not shutil.which("vercel"):
        raise SystemExit("Установите Vercel CLI: npm i -g vercel")
    token = os.environ.get("VERCEL_TOKEN")
    args = ["vercel", "deploy", "--prod", "--yes"]
    if token:
        args.extend(["--token", token])
    run(args)
    run(["vercel", "inspect", "--prod", "--json"], check=False)
    url = os.environ.get("VERCEL_URL") or os.environ.get("CLUSTER_STANDBY_URL", "")
    if not url:
        print("Задайте CLUSTER_STANDBY_URL=https://your-app.vercel.app после деплоя Vercel")
    return url.rstrip("/")


def deploy_koyeb() -> str:
    if not shutil.which("koyeb"):
        raise SystemExit("Установите Koyeb CLI: curl -fsSL https://cli.koyeb.com/install.sh | sh")
    token = os.environ.get("KOYEB_TOKEN")
    if token:
        run(["koyeb", "auth", "login", "--token", token])
    app = os.environ.get("KOYEB_APP", "food-mafia-bot")
    service = os.environ.get("KOYEB_SERVICE", "web")
    run(
        [
            "koyeb",
            "service",
            "create",
            app,
            service,
            "--docker",
            "Dockerfile",
            "--docker-builder",
            "buildkit",
            "--port",
            "8000:http",
            "--route",
            "/:8000",
            "--instance-type",
            "nano",
            "--regions",
            "was",
            "--env",
            "CLUSTER_ROLE=primary",
            "--env",
            "USE_WEBHOOK=1",
            "--env",
            f"CLUSTER_PEER_URL={os.environ.get('CLUSTER_STANDBY_URL', '')}",
            "--env",
            f"REDIS_URL={os.environ['REDIS_URL']}",
            "--env",
            f"DATABASE_URL={os.environ['DATABASE_URL']}",
            "--env",
            f"BOT_TOKEN={os.environ['BOT_TOKEN']}",
        ],
        check=False,
    )
    url = os.environ.get("KOYEB_PUBLIC_URL", "")
    if not url:
        print("Задайте KOYEB_PUBLIC_URL после создания сервиса в Koyeb")
    return url.rstrip("/")


def main() -> None:
    load_dotenv()
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"Не хватает переменных: {', '.join(missing)}")

    print("=== 1/4 Vercel standby ===")
    standby_url = deploy_vercel()
    if standby_url:
        os.environ["CLUSTER_STANDBY_URL"] = standby_url

    print("=== 2/4 Koyeb primary ===")
    primary_url = deploy_koyeb()
    if primary_url:
        os.environ["KOYEB_PUBLIC_URL"] = primary_url
        os.environ["WEBAPP_URL"] = primary_url

    print("=== 3/4 Health checks ===")
    for name, url in (("primary", primary_url), ("standby", standby_url)):
        if url:
            ok = check_health(url)
            print(f"  {name}: {url} -> {'OK' if ok else 'FAIL'}")

    print("=== 4/4 Telegram sync ===")
    if primary_url and shutil.which("python"):
        env = os.environ.copy()
        env["MINI_APP_URL"] = primary_url
        env["WEBHOOK_URL"] = primary_url
        env["SERVICE_URL"] = primary_url
        env["USE_WEBHOOK"] = "1"
        run([sys.executable, "scripts/sync_telegram.py"], cwd=ROOT)

    print("\nГотово. Проверьте:")
    print(f"  Primary (Koyeb):  {primary_url or '(задайте KOYEB_PUBLIC_URL)'}")
    print(f"  Standby (Vercel): {standby_url or '(задайте CLUSTER_STANDBY_URL)'}")
    print("  Статус кластера:  GET /api/cluster/status")


if __name__ == "__main__":
    main()
