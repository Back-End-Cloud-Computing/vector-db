async def test_insert_and_search(api_client):
    payload = {
        "items": [
            {
                "product_id": "p1",
                "embedding": [1.0, 0.0, 0.0],
                "metadata": {"brand": "acme"},
                "document": "produto um",
            },
            {
                "product_id": "p2",
                "embedding": [0.0, 1.0, 0.0],
                "metadata": {"brand": "acme"},
                "document": "produto dois",
            },
        ]
    }
    response = await api_client.post("/vector_db/insert", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["upserted"] == 2
    assert set(body["ids"]) == {"p1", "p2"}

    search_response = await api_client.post(
        "/vector_db/search", json={"embedding": [1.0, 0.0, 0.0], "n_results": 2}
    )
    assert search_response.status_code == 200
    search_body = search_response.json()
    assert search_body["ids"][0] == "p1"


async def test_upsert_overwrites_existing_record(api_client):
    await api_client.post(
        "/vector_db/insert",
        json={
            "items": [
                {"product_id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "v1"},
            ]
        },
    )
    response = await api_client.post(
        "/vector_db/insert",
        json={
            "items": [
                {"product_id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "v2"},
            ]
        },
    )
    assert response.status_code == 200

    search_response = await api_client.post("/vector_db/search", json={"embedding": [1.0, 0.0], "n_results": 1})
    assert search_response.json()["documents"][0] == "v2"


async def test_delete_by_ids(api_client):
    await api_client.post(
        "/vector_db/insert",
        json={"items": [{"product_id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "x"}]},
    )
    response = await api_client.post("/vector_db/delete", json={"ids": ["p1"]})
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    search_response = await api_client.post("/vector_db/search", json={"embedding": [1.0, 0.0], "n_results": 5})
    assert search_response.json()["ids"] == []


async def test_list_collections(api_client):
    response = await api_client.get("/vector_db/collections")
    assert response.status_code == 200
    assert "products" in response.json()["collections"]


async def test_health(api_client):
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
