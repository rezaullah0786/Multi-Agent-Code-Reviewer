import os
from fastapi.testclient import TestClient

from app.main import app
from app.retrieval.code_indexer import CodeIndexer
from app.retrieval.embeddings import LocalHashingEmbeddingProvider
from app.retrieval.qdrant_store import qdrant_store

client = TestClient(app)


def test_local_hashing_embedding_provider():
    provider = LocalHashingEmbeddingProvider(dimension=384)
    assert provider.get_dimension() == 384

    vec = provider.embed_query("def authenticate_user(username, password):")
    assert len(vec) == 384
    import math

    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-4

    texts = ["import os", "import sys"]
    vecs = provider.embed_texts(texts)
    assert len(vecs) == 2
    assert len(vecs[0]) == 384


def test_code_chunker():
    indexer = CodeIndexer(chunk_lines=10, chunk_overlap=2)
    sample_code = "\n".join([f"line_{i} = {i}" for i in range(25)])
    chunks = indexer.chunk_file("test.py", sample_code)
    assert len(chunks) >= 2
    assert chunks[0]["file_path"] == "test.py"
    assert chunks[0]["start_line"] == 1
    assert "language" in chunks[0]


def test_safe_path_validation():
    indexer = CodeIndexer()
    # Test valid directory
    valid, path = indexer.is_safe_path(os.path.dirname(__file__))
    assert valid is True

    # Test non-existent path
    invalid, msg = indexer.is_safe_path("C:/NonExistentPath_123456789")
    assert invalid is False
    assert "does not exist" in msg


def test_search_and_index_api():
    # Index current test directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    idx_res = client.post(
        "/api/v1/index",
        json={"directory_path": current_dir, "max_files": 10, "recursive": False},
    )
    assert idx_res.status_code == 200
    idx_data = idx_res.json()
    assert idx_data["status"] == "completed"
    assert "indexed_files" in idx_data

    # Status endpoint
    status_res = client.get("/api/v1/index/status")
    assert status_res.status_code == 200
    assert "storage_mode" in status_res.json()

    # Search endpoint
    search_res = client.post(
        "/api/v1/search",
        json={"query": "test_local_hashing_embedding", "limit": 3},
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert "results" in search_data
    assert "storage_mode" in search_data
