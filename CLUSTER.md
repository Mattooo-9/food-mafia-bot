# Active-Passive cluster (Koyeb + Vercel)

## Архитектура

| Узел | Платформа | Роль | Режим |
|------|-----------|------|--------|
| Primary | Koyeb | `CLUSTER_ROLE=primary` | 24/7 Docker + watchdog |
| Standby | Vercel | `CLUSTER_ROLE=standby` | Serverless + cron failover |

**Redis** (Upstash бесплатно) — распределённая блокировка `food-mafia:bot-leader`.  
Только один узел обрабатывает webhook Telegram.

**PostgreSQL** (Neon/Supabase) — общая БД для обоих узлов (`DATABASE_URL`).

## Быстрый старт

1. Создайте **Upstash Redis** → скопируйте `REDIS_URL`
2. Создайте **Neon Postgres** → `DATABASE_URL`
3. Зарегистрируйте [Koyeb](https://www.koyeb.com) и [Vercel](https://vercel.com)
4. Установите CLI: `npm i -g vercel`, [Koyeb CLI](https://www.koyeb.com/docs/build-and-deploy/cli/installation)

```bash
# .env
BOT_TOKEN=...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CRON_SECRET=случайная_строка
KOYEB_PUBLIC_URL=https://your-app.koyeb.app
CLUSTER_STANDBY_URL=https://your-app.vercel.app
CLUSTER_PEER_URL=https://your-app.vercel.app   # на Koyeb
```

5. Один деплой:

```bash
python scripts/deploy_cluster.py
```

## Ручной деплой

**Vercel (standby):**
```bash
vercel link
vercel env add BOT_TOKEN
vercel env add DATABASE_URL
vercel env add REDIS_URL
vercel env add CLUSTER_ROLE standby
vercel env add CLUSTER_PEER_URL https://your-app.koyeb.app
vercel env add CRON_SECRET
vercel deploy --prod
```

**Koyeb (primary):**
```bash
koyeb login
koyeb service create food-mafia-bot web --docker Dockerfile --port 8000:http
# Добавьте env в панели Koyeb (см. koyeb.yaml)
```

## Watchdog

- Внутри процесса: контроль памяти и критических ошибок (`WATCHDOG_*`)
- Снаружи (Docker): `scripts/watchdog_supervisor.py` перезапускает `main.py`

## Проверка

```bash
curl https://your-koyeb.app/health
curl https://your-koyeb.app/api/cluster/status
curl https://your-vercel.app/api/cluster/failover -H "X-Cron-Secret: $CRON_SECRET"
```

## Важно

- Регистрация аккаунтов Koyeb/Vercel выполняется **владельцем проекта** (нужна ваша почта и 2FA).
- Render/HuggingFace из старого CI можно оставить как дополнительный резерв.
