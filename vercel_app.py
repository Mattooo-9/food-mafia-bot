"""
Точка входа Vercel (standby): serverless FastAPI + webhook.
Переменные: CLUSTER_ROLE=standby, CLUSTER_PEER_URL=<koyeb url>, REDIS_URL, DATABASE_URL.
"""
import os

os.environ.setdefault("CLUSTER_ROLE", "standby")
os.environ.setdefault("USE_WEBHOOK", "1")

from mangum import Mangum

from backend.api.app import create_app
from main import attach_webhook_route, get_dispatcher

app = create_app()
attach_webhook_route(app, get_dispatcher())

handler = Mangum(app, lifespan="off")
