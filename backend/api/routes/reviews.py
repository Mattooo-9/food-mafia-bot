from fastapi import APIRouter, HTTPException

from backend.api.deps import CurrentUser, SessionDep
from backend.api.schemas import ReviewIn, ReviewOut
from backend.api.serializers import serialize_review
from backend.services import review_service
from backend.services.review_service import ReviewError

router = APIRouter(tags=["reviews"])


@router.post("/reviews", response_model=ReviewOut)
async def create_review(payload: ReviewIn, user: CurrentUser, session: SessionDep) -> ReviewOut:
    try:
        review = await review_service.create_review(
            session, user, payload.order_id, payload.rating, payload.text
        )
    except ReviewError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    review.buyer = user
    return serialize_review(review, viewer=user)
