from pydantic import BaseModel


class RecommendationItem(BaseModel):
    product_id: str
    score: float
    reasons: list[str]


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]
    strategy: str
