import chromadb
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import chromadb_client as chromadb_client_module


@pytest.fixture
def chroma_collection(monkeypatch):
    """Replaces the real (HTTP) ChromaDB client with an in-memory ephemeral
    one, so tests never need a running Chroma container.

    Chroma caches its underlying system by settings identity, so two
    `EphemeralClient()` instances created with identical default settings
    silently share state across tests. `reset()` (enabled via
    `allow_reset`) clears that shared state so each test starts empty.
    """
    settings = chromadb.config.Settings(allow_reset=True, anonymized_telemetry=False)
    client = chromadb.EphemeralClient(settings=settings)
    client.reset()
    collection = client.get_or_create_collection(name="products", metadata={"hnsw:space": "cosine"})
    monkeypatch.setattr(chromadb_client_module.chromadb_state, "client", client)
    monkeypatch.setattr(chromadb_client_module.chromadb_state, "collection", collection)
    yield collection


@pytest_asyncio.fixture
async def api_client(chroma_collection):
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
