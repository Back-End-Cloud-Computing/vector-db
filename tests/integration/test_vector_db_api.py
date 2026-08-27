async def test_insert_and_search(api_client):
    payload = {
        "collection_name": "products",
        "items": [
            {
                "id": "p1",
                "embedding": [1.0, 0.0, 0.0],
                "metadata": {"brand": "acme"},
                "document": "produto um",
            },
            {
                "id": "p2",
                "embedding": [0.0, 1.0, 0.0],
                "metadata": {"brand": "acme"},
                "document": "produto dois",
            },
        ],
    }
    response = await api_client.post("/vector_db/insert", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["upserted"] == 2
    assert set(body["ids"]) == {"p1", "p2"}

    search_response = await api_client.post(
        "/vector_db/search",
        json={"collection_name": "products", "embedding": [1.0, 0.0, 0.0], "n_results": 2},
    )
    assert search_response.status_code == 200
    search_body = search_response.json()
    assert search_body["ids"][0] == "p1"


async def test_upsert_overwrites_existing_record(api_client):
    await api_client.post(
        "/vector_db/insert",
        json={
            "collection_name": "products",
            "items": [
                {"id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "v1"},
            ],
        },
    )
    response = await api_client.post(
        "/vector_db/insert",
        json={
            "collection_name": "products",
            "items": [
                {"id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "v2"},
            ],
        },
    )
    assert response.status_code == 200

    search_response = await api_client.post(
        "/vector_db/search", json={"collection_name": "products", "embedding": [1.0, 0.0], "n_results": 1}
    )
    assert search_response.json()["documents"][0] == "v2"


async def test_delete_by_ids(api_client):
    await api_client.post(
        "/vector_db/insert",
        json={
            "collection_name": "products",
            "items": [{"id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "x"}],
        },
    )
    response = await api_client.post(
        "/vector_db/delete", json={"collection_name": "products", "ids": ["p1"]}
    )
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    search_response = await api_client.post(
        "/vector_db/search", json={"collection_name": "products", "embedding": [1.0, 0.0], "n_results": 5}
    )
    assert search_response.json()["ids"] == []


async def test_search_with_empty_where_is_treated_as_no_filter(api_client):
    """Chroma itself rejects `where={}` ("Expected where to have exactly one
    operator, got {}") instead of treating it as no filter - Swagger's
    auto-generated example pre-fills `where` with `{}`, so an unfiltered
    search must not break just because the caller left that default in."""
    await api_client.post(
        "/vector_db/insert",
        json={
            "collection_name": "products",
            "items": [{"id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "x"}],
        },
    )
    response = await api_client.post(
        "/vector_db/search",
        json={"collection_name": "products", "embedding": [1.0, 0.0], "n_results": 5, "where": {}},
    )
    assert response.status_code == 200
    assert response.json()["ids"] == ["p1"]


async def test_delete_with_empty_where_and_no_ids_is_rejected_not_silently_wiped(api_client):
    """Normalizing `where={}` to None must not turn into a delete-everything:
    Chroma itself still refuses when neither ids nor a real filter is given."""
    await api_client.post(
        "/vector_db/insert",
        json={
            "collection_name": "products",
            "items": [{"id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "x"}],
        },
    )
    response = await api_client.post("/vector_db/delete", json={"collection_name": "products", "where": {}})
    assert response.status_code == 503

    search_response = await api_client.post(
        "/vector_db/search", json={"collection_name": "products", "embedding": [1.0, 0.0], "n_results": 5}
    )
    assert search_response.json()["ids"] == ["p1"]


async def test_list_collections(api_client):
    response = await api_client.get("/vector_db/collections")
    assert response.status_code == 200
    assert "products" in response.json()["collections"]


async def test_count(api_client):
    await api_client.post(
        "/vector_db/insert",
        json={
            "collection_name": "products",
            "items": [
                {"id": "p1", "embedding": [1.0, 0.0], "metadata": {}, "document": "a"},
                {"id": "p2", "embedding": [0.0, 1.0], "metadata": {}, "document": "b"},
            ],
        },
    )
    response = await api_client.get("/vector_db/count", params={"collection_name": "products"})
    assert response.status_code == 200
    assert response.json() == {"collection_name": "products", "count": 2}


async def test_count_for_unknown_collection_is_zero(api_client):
    response = await api_client.get("/vector_db/count", params={"collection_name": "nunca-indexada"})
    assert response.status_code == 200
    assert response.json() == {"collection_name": "nunca-indexada", "count": 0}


async def test_health(api_client):
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
