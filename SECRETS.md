# Секреты и переменные для надёжного деплоя

## GitHub Secrets (обязательные)

| Secret | Назначение |
|---|---|
| `BOT_TOKEN` | Токен Telegram-бота |
| `ADMIN_ID` | Telegram ID админа |
| `WEBHOOK_SECRET` | Только `A-Za-z0-9_-` (без `+` и `=`) |

## GitHub Secrets (хотя бы один бэкенд)

| Secret | Платформа |
|---|---|
| `RENDER_API_KEY` | [Render API Keys](https://dashboard.render.com/u/settings#api-keys) |
| `HF_TOKEN` | [Hugging Face → Settings → Access Tokens](https://huggingface.co/settings/tokens) (write) |
| `NETLIFY_AUTH_TOKEN` | [Netlify → User settings → Applications](https://app.netlify.com/user/applications#personal-access-tokens) |

## GitHub Variables (рекомендуется)

| Variable | Пример | Зачем |
|---|---|---|
| `NETLIFY_URL` | `https://eda-ryadom.netlify.app` | Стабильный URL Mini App (не меняется) |
| `NETLIFY_SITE_ID` | из Netlify Site settings | Для CLI deploy |
| `BACKEND_URLS` | `https://food-mafia-bot.onrender.com,https://user-food-mafia-bot.hf.space` | Health-check по приоритету |
| `HF_SPACE` | `Mattooo-9/food-mafia-bot` | Имя Space на HF |
| `RENDER_URL` | `https://food-mafia-bot.onrender.com` | Keep-alive |

## Как это работает (каждый push в `main`)

1. **Сборка** Mini App (кэш npm, быстро)
2. **Параллельно**: Render + Hugging Face
3. **Health-check** — выбирается живой бэкенд
4. **Netlify** — статика + прокси `/api`, `/uploads`, `/tg/webhook` на бэкенд
5. **sync_telegram.py** — кнопка Mini App → Netlify (стабильно), webhook → тот же URL (прокси на бэкенд)
6. **Keep-alive** каждые 10 мин пингует все URL

## Локально

`.env` — только на ПК, в git не попадает.

```env
USE_WEBHOOK=0
PORT=8001
WEBAPP_URL=https://your-tunnel.lhr.life
```

## Платформы

| Платформа | Роль | Карта |
|---|---|---|
| **Netlify** | Стабильный Mini App (CDN) | Нет |
| **Render** | Бэкенд + бот (webhook) | Нет |
| **Hugging Face Space** | Запасной бэкенд (Docker) | Нет |
| localhost.run | Только для отладки | Нет |

## Безопасность

- Токены из чата → `/revoke` в @BotFather, перевыпустить API-ключи
- Webhook: заголовок `X-Telegram-Bot-Api-Secret-Token`
- `/docs` отключены при `USE_WEBHOOK=1`

## Важно

Пока бот в облаке с webhook — **не запускайте** `python main.py` локально (конфликт с Telegram).
