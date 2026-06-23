from fastapi import APIRouter

from backend.api.routes import ai, cluster, cooks, favorites, foods, orders, reviews, subscriptions, uploads, users, wishes

api_router = APIRouter(prefix="/api")
api_router.include_router(cluster.router)
api_router.include_router(ai.router)
api_router.include_router(wishes.router)
api_router.include_router(cooks.router)
api_router.include_router(favorites.router)
api_router.include_router(foods.router)
api_router.include_router(orders.router)
api_router.include_router(reviews.router)
api_router.include_router(subscriptions.router)
api_router.include_router(uploads.router)
api_router.include_router(users.router)
