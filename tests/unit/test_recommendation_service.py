import pytest

from app.core.exceptions import ProductVectorNotFoundError
from app.services import recommendation_service


async def test_recommend_similar_products_excludes_reference(chroma_collection):
    chroma_collection.upsert(
        ids=["p1", "p2", "p3"],
        embeddings=[[1.0, 0.0], [0.95, 0.05], [0.0, 1.0]],
        metadatas=[{"product_id": "p1"}, {"product_id": "p2"}, {"product_id": "p3"}],
        documents=["a", "b", "c"],
    )
    items = await recommendation_service.recommend_similar_products("p1", limit=10)
    ids = [item.product_id for item in items]
    assert "p1" not in ids
    assert ids[0] == "p2"


async def test_recommend_similar_products_raises_when_not_indexed(chroma_collection):
    with pytest.raises(ProductVectorNotFoundError):
        await recommendation_service.recommend_similar_products("missing")


async def test_recommend_for_user_falls_back_when_no_signals(chroma_collection):
    chroma_collection.upsert(
        ids=["p1"], embeddings=[[1.0, 0.0]], metadatas=[{"product_id": "p1"}], documents=["a"]
    )
    items = await recommendation_service.recommend_for_user("u1", limit=5)
    assert len(items) == 1
    assert items[0].product_id == "p1"
