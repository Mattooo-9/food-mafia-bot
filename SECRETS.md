# Куда класть секреты (токены НЕ коммитить в git)

## Локально (только ваш ПК)

Файл **`.env`** в корне проекта — уже в `.gitignore`.

```
BOT_TOKEN=...
ADMIN_ID=8017348770
USE_WEBHOOK=0
```

## Render.com (основной облачный деплой)

1. Откройте: https://render.com/deploy?repo=https://github.com/Mattooo-9/food-mafia-bot  
2. При создании сервиса введите в **Environment Variables**:
   - `BOT_TOKEN` — токен от @BotFather
   - `ADMIN_ID` — `8017348770`
3. Остальное подставится из `render.yaml`:
   - `USE_WEBHOOK=1`
   - `DATABASE_URL` — из PostgreSQL Render
   - `RENDER_EXTERNAL_URL` — Render добавит сам (URL Mini App)

**Не добавляйте** `WEBAPP_URL` на Render — достаточно `RENDER_EXTERNAL_URL`.

## Railway.app (альтернатива)

В проекте → **Variables**:

| Переменная | Значение |
|---|---|
| `BOT_TOKEN` | токен бота |
| `ADMIN_ID` | `8017348770` |
| `USE_WEBHOOK` | `1` |
| `PUBLIC_URL` | `https://<ваш-домен>.up.railway.app` |

## GitHub (только для пингера, не секреты)

Settings → Secrets and variables → Actions → **Variables**:

- `RENDER_URL` = `https://food-mafia-bot.onrender.com` (ваш реальный URL после деплоя)

Токен бота в GitHub **не нужен**.

## Что делает приложение само при старте в облаке

- Webhook Telegram → `/tg/webhook`
- Кнопка меню «Еда Рядом» → Mini App
- Keep-alive пинг `/health` каждые 10 мин

## Важно

Пока бот работает в облаке — **не запускайте** `python main.py` локально (сломает webhook).
