import asyncio
import logging
from typing import Any

import chromadb

from app.core.config import get_settings
from app.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class ChromaDBState:
    """Holds the lazily-initialized Chroma client/collection for the app lifespan.

    Typed as `Any` deliberately: chromadb's client/collection classes live under
    internal, version-sensitive module paths, so depending on them directly here
    would couple this module to chromadb's implementation details rather than
    its public `chromadb.HttpClient(...)` entry point used below.
    """

    client: Any | None = None
    collection: Any | None = None


chromadb_state = ChromaDBState()


def connect_to_chromadb() -> None:
    settings = get_settings()
    chromadb_state.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    chromadb_state.collection = chromadb_state.client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info("Connected to ChromaDB at %s:%s", settings.chroma_host, settings.chroma_port)


def get_products_collection() -> Any:
    if chromadb_state.collection is None:
        raise RuntimeError("ChromaDB connection has not been initialized")
    return chromadb_state.collection


def get_client() -> Any:
    if chromadb_state.client is None:
        raise RuntimeError("ChromaDB connection has not been initialized")
    return chromadb_state.client


async def list_collections() -> list[str]:
    def _list() -> list[str]:
        try:
            return [c.name for c in get_client().list_collections()]
        except Exception as exc:  # noqa: BLE001 - normalize any backend failure
            raise VectorStoreError(f"Failed to list collections: {exc}") from exc

    return await asyncio.to_thread(_list)


async def upsert_batch(
    ids: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
    documents: list[str],
) -> None:
    """Upsert (insert or replace) a batch of product vectors, keyed by product_id."""

    def _upsert() -> None:
        try:
            get_products_collection().upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to upsert batch: {exc}") from exc

    await asyncio.to_thread(_upsert)


async def query_similar(
    embedding: list[float],
    n_results: int = 10,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def _query() -> dict[str, Any]:
        try:
            return get_products_collection().query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where,
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to query ChromaDB: {exc}") from exc

    return await asyncio.to_thread(_query)


async def get_embedding(product_id: str) -> list[float] | None:
    """Fetch a previously indexed embedding by id, without recomputing it."""

    def _get() -> list[float] | None:
        try:
            result = get_products_collection().get(ids=[product_id], include=["embeddings"])
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to fetch embedding for '{product_id}': {exc}") from exc
        embeddings = result.get("embeddings")
        if embeddings is None or len(embeddings) == 0:
            return None
        return list(embeddings[0])

    return await asyncio.to_thread(_get)


async def peek_ids(limit: int) -> list[str]:
    """Return up to `limit` arbitrary indexed ids, used as a cold-start fallback
    when no behavioral signal yields any candidate."""

    def _peek() -> list[str]:
        try:
            result = get_products_collection().get(limit=limit)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to peek products: {exc}") from exc
        return list(result.get("ids", []))

    return await asyncio.to_thread(_peek)


async def delete_vectors(ids: list[str] | None = None, where: dict[str, Any] | None = None) -> None:
    def _delete() -> None:
        try:
            get_products_collection().delete(ids=ids, where=where)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to delete vectors: {exc}") from exc

    await asyncio.to_thread(_delete)
