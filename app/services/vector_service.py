from app.database import chromadb_client
from app.schemas.vector import DeleteRequest, InsertRequest, SearchRequest, SearchResponse


async def insert_batch(payload: InsertRequest) -> tuple[int, list[str]]:
    ids = [item.product_id for item in payload.items]
    embeddings = [item.embedding for item in payload.items]
    # Chroma rejects empty metadata dicts, so product_id is always included as
    # a minimal, always-present filterable field.
    metadatas = [{"product_id": item.product_id, **item.metadata} for item in payload.items]
    documents = [item.document for item in payload.items]
    await chromadb_client.upsert_batch(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
    return len(ids), ids


async def search(payload: SearchRequest) -> SearchResponse:
    result = await chromadb_client.query_similar(
        embedding=payload.embedding, n_results=payload.n_results, where=payload.where
    )
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    documents = result.get("documents", [[]])[0]
    return SearchResponse(ids=ids, distances=distances, metadatas=metadatas, documents=documents)


async def delete(payload: DeleteRequest) -> bool:
    await chromadb_client.delete_vectors(ids=payload.ids, where=payload.where)
    return True
