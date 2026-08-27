import logging

from app.core.exceptions import ProductVectorNotFoundError
from app.database import chromadb_client
from app.integrations import get_cart_client, get_customer_client, get_order_client
from app.schemas.recommendation import RecommendationItem

logger = logging.getLogger(__name__)

# Behavioral signals are weighted rather than relying purely on vector
# similarity, so purchase/view/cart history can shift recommendations even
# when content similarity alone would rank items differently.
WEIGHT_PURCHASE_HISTORY = 0.35
WEIGHT_VIEWED_PRODUCTS = 0.25
WEIGHT_CART = 0.25
WEIGHT_SIMILAR_USERS = 0.15

PRODUCTS_COLLECTION = "products"


async def recommend_similar_products(product_id: str, limit: int = 10) -> list[RecommendationItem]:
    """Content-based recommendation: nearest neighbors of a product's own
    already-indexed embedding (never recomputed here)."""
    embedding = await chromadb_client.get_embedding(PRODUCTS_COLLECTION, product_id)
    if embedding is None:
        raise ProductVectorNotFoundError(product_id)

    result = await chromadb_client.query_similar(PRODUCTS_COLLECTION, embedding, n_results=limit + 1)
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]

    items: list[RecommendationItem] = []
    for pid, distance in zip(ids, distances):
        if pid == product_id:
            continue
        similarity = max(0.0, 1.0 - distance)
        items.append(
            RecommendationItem(
                product_id=pid,
                score=round(similarity, 4),
                reasons=["similaridade de conteudo com o produto de referencia"],
            )
        )
        if len(items) >= limit:
            break
    return items


async def recommend_for_user(user_id: str, limit: int = 10) -> list[RecommendationItem]:
    """Personalized recommendation combining multiple behavioral signals with
    content similarity. Cart/Order/Customer data is mocked today (those
    microservices aren't integrated yet) behind `app.integrations`, so
    swapping in real HTTP clients later requires no change here.
    """
    cart_ids = await get_cart_client().get_cart_product_ids(user_id)
    purchased_ids = await get_order_client().get_purchased_product_ids(user_id)
    viewed_ids = await get_customer_client().get_viewed_product_ids(user_id)
    similar_users_ids = await get_customer_client().get_similar_users_purchases(user_id)

    weighted_signals = {
        "historico de compras": (purchased_ids, WEIGHT_PURCHASE_HISTORY),
        "produtos visualizados": (viewed_ids, WEIGHT_VIEWED_PRODUCTS),
        "carrinho atual": (cart_ids, WEIGHT_CART),
        "usuarios com comportamento similar": (similar_users_ids, WEIGHT_SIMILAR_USERS),
    }

    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}

    for label, (reference_ids, weight) in weighted_signals.items():
        for reference_id in reference_ids:
            try:
                neighbors = await recommend_similar_products(reference_id, limit=5)
            except ProductVectorNotFoundError:
                continue
            for item in neighbors:
                scores[item.product_id] = scores.get(item.product_id, 0.0) + item.score * weight
                reasons.setdefault(item.product_id, []).append(f"relacionado a produto de {label}")

    already_owned_or_in_cart = set(cart_ids) | set(purchased_ids)
    ranked = sorted(
        ((pid, score) for pid, score in scores.items() if pid not in already_owned_or_in_cart),
        key=lambda pair: pair[1],
        reverse=True,
    )[:limit]

    if not ranked:
        return await _fallback_popular_products(limit)

    return [
        RecommendationItem(product_id=pid, score=round(score, 4), reasons=reasons.get(pid, []))
        for pid, score in ranked
    ]


async def _fallback_popular_products(limit: int) -> list[RecommendationItem]:
    """Cold-start fallback: with no behavioral signal at all (new/anonymous
    user, mocks returning empty data), surface arbitrary indexed products
    instead of an empty response."""
    ids = await chromadb_client.peek_ids(PRODUCTS_COLLECTION, limit)
    return [RecommendationItem(product_id=pid, score=0.0, reasons=["produto em destaque"]) for pid in ids]
