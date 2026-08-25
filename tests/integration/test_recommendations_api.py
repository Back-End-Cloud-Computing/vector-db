async def test_similar_products(api_client):
    await api_client.post(
        "/vector_db/insert",
        json={
            "items": [
                {"product_id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "a"},
                {"product_id": "p2", "embedding": [0.9, 0.1], "metadata": {}, "document": "b"},
            ]
        },
    )
    response = await api_client.get("/vector_db/recommendations/products/p1/similar")
    assert response.status_code == 200
    body = response.json()
    assert body["strategy"] == "content_similarity"
    assert body["items"][0]["product_id"] == "p2"


async def test_similar_products_not_indexed_returns_404(api_client):
    response = await api_client.get("/vector_db/recommendations/products/missing/similar")
    assert response.status_code == 404


async def test_recommendations_for_user_falls_back_to_popular(api_client):
    await api_client.post(
        "/vector_db/insert",
        json={"items": [{"product_id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "a"}]},
    )
    response = await api_client.get("/vector_db/recommendations/users/u1")
    assert response.status_code == 200
    body = response.json()
    assert body["strategy"] == "hybrid_behavioral_signals"
    assert body["items"][0]["product_id"] == "p1"
    assert body["items"][0]["reasons"] == ["produto em destaque"]
