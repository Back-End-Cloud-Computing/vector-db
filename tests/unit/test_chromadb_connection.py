import pytest

from app.database import chromadb_client


@pytest.fixture(autouse=True)
def no_wait_between_retries(monkeypatch):
    monkeypatch.setattr(chromadb_client._create_client.retry, "sleep", lambda seconds: None)
    yield
    chromadb_client.chromadb_state.client = None


def test_connect_waits_until_chroma_is_ready(monkeypatch):
    attempts = []
    ready_client = object()

    def http_client(host, port):
        attempts.append((host, port))
        if len(attempts) < 3:
            raise ValueError("Could not connect to a Chroma server. Are you sure it is running?")
        return ready_client

    monkeypatch.setattr(chromadb_client.chromadb, "HttpClient", http_client)

    chromadb_client.connect_to_chromadb()

    assert len(attempts) == 3
    assert chromadb_client.chromadb_state.client is ready_client


def test_connect_gives_up_after_the_retry_window(monkeypatch):
    def never_ready(host, port):
        raise ValueError("Could not connect to a Chroma server. Are you sure it is running?")

    monkeypatch.setattr(chromadb_client.chromadb, "HttpClient", never_ready)
    monkeypatch.setattr(chromadb_client._create_client.retry, "stop", chromadb_client.tenacity.stop_after_attempt(3))

    with pytest.raises(ValueError, match="Could not connect"):
        chromadb_client.connect_to_chromadb()
