FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY database/ ./database/
COPY main.py alembic.ini ./
COPY --from=frontend /frontend/dist ./frontend/dist

RUN mkdir -p uploads database

EXPOSE 8000
CMD ["python", "main.py"]
