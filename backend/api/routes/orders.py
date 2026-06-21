from fastapi import APIRouter, HTTPException

from backend.api.deps import CurrentCook, CurrentUser, SessionDep
from backend.api.schemas import OrderIn, OrderOut, OrderStatusIn
from backend.api.serializers import serialize_order
from backend.models import OrderStatus
from backend.services import order_service, review_service
from backend.services.order_service import OrderError

router = APIRouter(tags=["orders"])


@router.post("/orders", response_model=OrderOut)
async def create_order(payload: OrderIn, user: CurrentUser, session: SessionDep) -> OrderOut:
    try:
        order = await order_service.create_order(
            session, user, payload.food_id, payload.quantity, payload.comment,
            payment_method=payload.payment_method.value,
        )
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_order(order)


@router.get("/orders", response_model=list[OrderOut])
async def my_orders(user: CurrentUser, session: SessionDep) -> list[OrderOut]:
    orders = await order_service.get_buyer_orders(session, user)
    result = []
    for order in orders:
        review = await review_service.get_order_review(session, order.id)
        result.append(serialize_order(order, has_review=review is not None))
    return result


@router.get("/cook/orders", response_model=list[OrderOut])
async def cook_orders(cook: CurrentCook, session: SessionDep) -> list[OrderOut]:
    orders = await order_service.get_cook_orders(session, cook)
    return [serialize_order(o) for o in orders]


@router.post("/orders/{order_id}/status", response_model=OrderOut)
async def change_order_status(
    order_id: int, payload: OrderStatusIn, user: CurrentUser, session: SessionDep
) -> OrderOut:
    try:
        order = await order_service.change_status(session, order_id, payload.status, user)
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_order(order)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(order_id: int, user: CurrentUser, session: SessionDep) -> OrderOut:
    try:
        order = await order_service.change_status(session, order_id, OrderStatus.CANCELLED, user)
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_order(order)
