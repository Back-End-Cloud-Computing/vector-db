import chromadb
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import CurrentUser, get_current_user
from app.database import chromadb_client as chromadb_client_module

FAKE_USER = CurrentUser(id="11111111-1111-1111-1111-111111111111", email="teste@ganjj.com", role="CLIENTE")


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
    monkeypatch.setattr(chromadb_client_module.chromadb_state, "collections", {"products": collection})
    yield collection


@pytest_asyncio.fixture
async def api_client(chroma_collection):
    """Authenticated API client: overrides `get_current_user` so existing
    tests don't need to carry a real token. Auth enforcement itself is
    covered separately in `tests/integration/test_auth.py`, against the
    real dependency."""
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_current_user, None)
