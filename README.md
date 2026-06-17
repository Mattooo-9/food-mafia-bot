# Еда Рядом — Telegram Mini App + Bot

Локальный маркетплейс домашней еды по геолокации внутри Telegram.

- **Mini App** (React + TypeScript + Telegram WebApp SDK) — основной продукт: лента блюд, заказы, избранное, кабинет повара.
- **Bot** (Aiogram 3.x) — авторизация, геолокация, регистрация повара, уведомления о заказах и новых блюдах.
- **Backend** (FastAPI + SQLAlchemy 2.x + Alembic) — API, геопоиск (Haversine), рейтинги, комиссия платформы 1%.

## Возможности

**Покупатель:** вход по Telegram ID, геолокация, лента (рядом / новые / популярное / дешёвое / быстрые), фильтры (расстояние 500м–10км, цена, рейтинг, категория), заказы со статусами, избранное (блюда и повара), подписки на поваров, отзывы 1–5 после заказа.

**Повар:** профиль (название, описание, фото, онлайн/оффлайн), управление блюдами (создание, редактирование, удаление, скрытие, порции), управление заказами из Mini App и прямо из уведомлений бота (inline-кнопки).

**Платформа:** при переходе заказа в `DELIVERED` автоматически начисляется комиссия 1% от `total_price` в таблицу `platform_balance` (ровно один раз на заказ).

## Запуск (локально)

Требуется Python 3.12+ и Node.js 20+.

```bash
# 1. Настройки
cp .env.example .env   # впишите BOT_TOKEN и ADMIN_ID

# 2. Бэкенд
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

# 3. Фронтенд (Mini App)
cd frontend
npm install
npm run build
cd ..

# 4. Старт (API + бот одним процессом)
python main.py
```

API поднимется на `http://localhost:8000` и сам раздаёт собранный Mini App из `frontend/dist`.

## Деплой (надёжно, 3 платформы + автосинхронизация бота)

Каждый **push в `main`** запускает [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml):

| Платформа | Роль |
|---|---|
| **Netlify** | Стабильный URL Mini App (CDN), прокси API на живой бэкенд |
| **Render** | Основной бэкенд + бот (webhook) |
| **Hugging Face Space** | Запасной бэкенд (Docker) |

После деплоя CI сам выбирает здоровый бэкенд, публикует Mini App и вызывает `scripts/sync_telegram.py` (кнопка + webhook).

Секреты и переменные — в [`SECRETS.md`](SECRETS.md).

Keep-alive пингует все URL каждые 10 минут.

## Деплой в облако (Render, бесплатно, 24/7)

Проект готов к развёртыванию в один клик — в репозитории есть `render.yaml` (web-сервис + PostgreSQL):

1. Откройте: **https://render.com/deploy?repo=https://github.com/Mattooo-9/food-mafia-bot**
2. Войдите через GitHub.
3. Вставьте `BOT_TOKEN` (и `ADMIN_ID`) когда спросит — и нажмите Apply/Deploy.

После деплоя всё настраивается **автоматически** при старте:
- бот переключается в webhook-режим (`USE_WEBHOOK=1`, адрес берётся из `RENDER_EXTERNAL_URL`);
- кнопка меню «Еда Рядом» с Mini App устанавливается сама — BotFather не нужен.

⚠️ Пока работает облачная версия, **не запускайте** `python main.py` локально — локальный бот перехватит обновления и сломает webhook.

Особенности бесплатного тарифа Render: сервис засыпает после 15 минут без трафика (просыпается от сообщения боту или открытия Mini App за ~30–60 сек); загруженные фото стираются при редеплое; бесплатная PostgreSQL живёт 30 дней (потом нужно пересоздать или перейти на платный план).

## Запуск (Docker)

```bash
docker compose up --build
```

Поднимает приложение + PostgreSQL 16.

## Подключение Mini App к боту

Telegram требует **публичный HTTPS-адрес**:

1. Пробросьте порт наружу, например: `cloudflared tunnel --url http://localhost:8000` (или ngrok).
2. Полученный `https://...` адрес впишите в `.env` → `WEBAPP_URL=` и перезапустите.
3. В [@BotFather](https://t.me/BotFather): `/setmenubutton` → выберите бота → укажите тот же URL. 

После этого кнопка «🍲 Открыть Еда Рядом» появится в боте (`/start`, `/app`).

## Миграции (Alembic)

Таблицы создаются автоматически при первом старте (для разработки). Для продакшена (PostgreSQL):

```bash
alembic upgrade head
```

## Структура

```
main.py                  # точка входа: FastAPI + бот в одном процессе
backend/
  config/                # настройки (pydantic-settings, .env)
  database/              # движок, сессии, Base
  models/                # User, Food, Order, Review, Favorite*, Subscription, PlatformBalance
  services/              # бизнес-логика: заказы, еда, рейтинг, избранное, подписки, уведомления
  api/                   # FastAPI: схемы, роутеры, auth по initData, сериализация
  handlers/              # aiogram-хендлеры: /start, геолокация, регистрация повара, заказы
  states/                # FSM-состояния (регистрация повара)
  utils/                 # Haversine, валидация initData, rate limiting, логирование
database/
  migrations/            # Alembic
frontend/
  src/                   # React + TS Mini App
```

## Безопасность и надёжность

- Авторизация: HMAC-валидация `initData` Telegram WebApp (заголовок `X-Telegram-Init-Data`).
- Rate limiting: 120 запросов/мин на пользователя (sliding window).
- Защита от дублей заказов: одинаковый новый заказ блокируется в течение 2 минут.
- Валидация данных: Pydantic-схемы на всех входах, контроль переходов статусов заказа.
- Логирование и глобальный обработчик ошибок.
