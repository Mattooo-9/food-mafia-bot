# Секреты — куда класть

## ✅ Уже в GitHub Secrets (Actions)

| Secret | Назначение |
|---|---|
| `BOT_TOKEN` | Токен Telegram-бота |
| `ADMIN_ID` | `8017348770` |
| `WEBHOOK_SECRET` | Отдельный секрет webhook |

## ⚠️ Нужен один раз для автодеплоя (бесплатно, без карты)

1. Зарегистрируйтесь на **https://render.com** (GitHub login, карта не нужна).
2. **Account Settings → API Keys** → Create API Key.
3. Добавьте в GitHub:
   ```powershell
   gh secret set RENDER_API_KEY
   ```
4. Запустите деплой:
   ```powershell
   gh workflow run deploy-render-api
   ```

Скрипт `scripts/deploy_render.py` создаст free web service + PostgreSQL из `render.yaml` логики, пропишет env и задеплоит.

## Локально

Файл `.env` — только на ПК, в git не попадает.

## Почему не Railway / Fly.io

- **Railway** — trial истёк на аккаунте.
- **Fly.io** — требует карту даже на free tier.

## Render (рекомендуется, бесплатно)

- Web service free + PostgreSQL free 30 дней
- `RENDER_EXTERNAL_URL` подставляется сам
- Webhook + кнопка Mini App настраиваются при старте

## Безопасность

- Токен светился в чате → **/revoke** в @BotFather и обновить секреты.
- Webhook защищён `X-Telegram-Bot-Api-Secret-Token`.
- `/docs` отключены в облаке.

## Важно

Пока бот в облаке — **не запускайте** `python main.py` локально.
