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
