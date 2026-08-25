from fastapi import APIRouter, Query

from app.schemas.recommendation import RecommendationResponse
from app.services import recommendation_service

router = APIRouter(prefix="/vector_db/recommendations", tags=["recommendations"])


@router.get("/products/{product_id}/similar", response_model=RecommendationResponse)
async def similar_products(product_id: str, limit: int = Query(10, ge=1, le=50)) -> RecommendationResponse:
    items = await recommendation_service.recommend_similar_products(product_id, limit=limit)
    return RecommendationResponse(items=items, strategy="content_similarity")


@router.get("/users/{user_id}", response_model=RecommendationResponse)
async def recommendations_for_user(user_id: str, limit: int = Query(10, ge=1, le=50)) -> RecommendationResponse:
    """Combines purchase history, viewed products, cart contents, and similar-user
    behavior (all mocked today via `app.integrations`) with content similarity."""
    items = await recommendation_service.recommend_for_user(user_id, limit=limit)
    return RecommendationResponse(items=items, strategy="hybrid_behavioral_signals")
