from fastapi import APIRouter, HTTPException

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import CookOut, OkOut
from backend.api.serializers import serialize_cook
from backend.services import favorite_service, subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("", response_model=list[CookOut])
async def my_subscriptions(user: CurrentUser, session: SessionDep) -> list[CookOut]:
    cooks = await subscription_service.get_subscriptions(session, user)
    favorite_ids = await favorite_service.get_favorite_cook_ids(session, user)
    result = []
    for cook in cooks:
        out = serialize_cook(cook, favorite_ids=favorite_ids)
        out.is_subscribed = True
        result.append(out)
    return result


@router.post("/{cook_id}", response_model=OkOut)
async def subscribe(cook_id: int, user: CurrentUser, session: SessionDep) -> OkOut:
    ok = await subscription_service.subscribe(session, user, cook_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Невозможно подписаться на этого повара")
    return OkOut()


@router.delete("/{cook_id}", response_model=OkOut)
async def unsubscribe(cook_id: int, user: CurrentUser, session: SessionDep) -> OkOut:
    await subscription_service.unsubscribe(session, user, cook_id)
    return OkOut()
