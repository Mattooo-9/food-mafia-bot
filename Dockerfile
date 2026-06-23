FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV USE_WEBHOOK=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY database/ ./database/
COPY main.py alembic.ini vercel_app.py ./
COPY scripts/ ./scripts/
COPY --from=frontend /frontend/dist ./frontend/dist

RUN mkdir -p uploads database /data

ENV CLUSTER_ROLE=primary
ENV USE_WEBHOOK=1
ENV WATCHDOG_ENABLED=1

EXPOSE 8000
CMD ["python", "scripts/watchdog_supervisor.py"]
