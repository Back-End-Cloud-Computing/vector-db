import asyncio
import logging
from typing import Any

import chromadb

from app.core.config import get_settings
from app.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class ChromaDBState:
    """Holds the lazily-initialized Chroma client/collections for the app lifespan.

    Typed as `Any` deliberately: chromadb's client/collection classes live under
    internal, version-sensitive module paths, so depending on them directly here
    would couple this module to chromadb's implementation details rather than
    its public `chromadb.HttpClient(...)` entry point used below.
    """

    client: Any | None = None
    collections: dict[str, Any]

    def __init__(self) -> None:
        self.collections = {}


chromadb_state = ChromaDBState()


def connect_to_chromadb() -> None:
    settings = get_settings()
    chromadb_state.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    logger.info("Connected to ChromaDB at %s:%s", settings.chroma_host, settings.chroma_port)


def get_collection(collection_name: str) -> Any:
    """Returns the Chroma collection for `collection_name`, creating it on first
    use and caching it for the life of the process. Every caller must state
    which collection it wants - there is no implicit/default collection, so
    each entity type (products, and whatever comes next) stays isolated."""
    cached = chromadb_state.collections.get(collection_name)
    if cached is not None:
        return cached
    collection = get_client().get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    chromadb_state.collections[collection_name] = collection
    return collection


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


async def count(collection_name: str) -> int:
    def _count() -> int:
        try:
            return get_collection(collection_name).count()
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to count collection '{collection_name}': {exc}") from exc

    return await asyncio.to_thread(_count)


async def upsert_batch(
    collection_name: str,
    ids: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
    documents: list[str],
) -> None:
    """Upsert (insert or replace) a batch of vectors, keyed by id, into `collection_name`."""

    def _upsert() -> None:
        try:
            get_collection(collection_name).upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to upsert batch: {exc}") from exc

    await asyncio.to_thread(_upsert)


async def query_similar(
    collection_name: str,
    embedding: list[float],
    n_results: int = 10,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def _query() -> dict[str, Any]:
        try:
            return get_collection(collection_name).query(
                query_embeddings=[embedding],
                n_results=n_results,
                # Chroma rejects `where={}` ("Expected where to have exactly one
                # operator, got {}") instead of treating it as no filter, so an
                # empty dict is normalized to None here for every caller.
                where=where or None,
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to query ChromaDB: {exc}") from exc

    return await asyncio.to_thread(_query)


async def get_embedding(collection_name: str, entity_id: str) -> list[float] | None:
    """Fetch a previously indexed embedding by id, without recomputing it."""

    def _get() -> list[float] | None:
        try:
            result = get_collection(collection_name).get(ids=[entity_id], include=["embeddings"])
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to fetch embedding for '{entity_id}': {exc}") from exc
        embeddings = result.get("embeddings")
        if embeddings is None or len(embeddings) == 0:
            return None
        return list(embeddings[0])

    return await asyncio.to_thread(_get)


async def peek_ids(collection_name: str, limit: int) -> list[str]:
    """Return up to `limit` arbitrary indexed ids, used as a cold-start fallback
    when no behavioral signal yields any candidate."""

    def _peek() -> list[str]:
        try:
            result = get_collection(collection_name).get(limit=limit)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to peek collection '{collection_name}': {exc}") from exc
        return list(result.get("ids", []))

    return await asyncio.to_thread(_peek)


async def delete_vectors(
    collection_name: str, ids: list[str] | None = None, where: dict[str, Any] | None = None
) -> None:
    def _delete() -> None:
        try:
            # Same `where={}` normalization as query_similar. Chroma still
            # refuses the call if both `ids` and `where` end up empty ("At
            # least one of ids, where, or where_document must be provided"),
            # so this can't turn into an accidental delete-everything.
            get_collection(collection_name).delete(ids=ids, where=where or None)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to delete vectors: {exc}") from exc

    await asyncio.to_thread(_delete)
