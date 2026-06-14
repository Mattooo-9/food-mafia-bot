# Куда класть секреты

## ✅ Уже настроено автоматически

**GitHub Repository Secrets** (через `gh`, в коде не хранятся):
- `BOT_TOKEN`
- `ADMIN_ID`
- `WEBHOOK_SECRET` — отдельный секрет для webhook (не равен токену бота)

**GitHub Variables:**
- `RENDER_URL` = `https://food-mafia-bot.onrender.com`

## Локально

Файл **`.env`** — только на вашем ПК, в git не попадает.

## Render.com (облако 24/7)

1. Откройте: https://render.com/deploy?repo=https://github.com/Mattooo-9/food-mafia-bot  
2. В Environment Variables вставьте:
   - `BOT_TOKEN` — из GitHub Secrets или BotFather
   - `ADMIN_ID` = `8017348770`
   - `WEBHOOK_SECRET` — скопируйте из GitHub → Settings → Secrets → Actions → WEBHOOK_SECRET (показать нельзя, только при создании; при необходимости сгенерируйте новый и обновите в Render + GitHub)
3. После деплоя: Settings → Deploy Hook → скопируйте URL → GitHub Secrets → `RENDER_DEPLOY_HOOK` (для автодеплоя при push)

Render сам добавит `RENDER_EXTERNAL_URL` и `DATABASE_URL`.

## Railway (альтернатива)

Variables: `BOT_TOKEN`, `ADMIN_ID`, `USE_WEBHOOK=1`, `PUBLIC_URL`, `WEBHOOK_SECRET`

## Безопасность

- Токен бота **светился в чате** — рекомендуется **/revoke** старый и выдать новый в @BotFather, затем обновить `.env`, GitHub Secrets и Render.
- Webhook защищён заголовком `X-Telegram-Bot-Api-Secret-Token`.
- В продакшене отключены `/docs` и `/redoc`.
- Rate limit на `/api/*` и `/tg/webhook`.
- Security headers (CSP, HSTS, X-Frame-Options).

## Важно

Пока бот в облаке — **не запускайте** `python main.py` локально.
