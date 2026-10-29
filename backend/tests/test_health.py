from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "ast_engine" in data["components"]
    assert "vector_store" in data["components"]
    assert "llm_provider" in data["components"]
    assert "github_integration" in data["components"]
    assert data["mode"] in ("local-demonstration", "production")


def test_health_without_llm_key():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    llm = data["components"]["llm_provider"]
    assert "status_message" in llm
    assert "is_configured" in llm
