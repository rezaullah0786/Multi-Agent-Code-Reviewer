from fastapi.testclient import TestClient
from app.main import app
from app.schemas.review import GateStatus

client = TestClient(app)


def test_valid_code_review_request():
    payload = {
        "code": "def hello():\n    return 'world'\n",
        "file_path": "hello.py",
        "scope": "ALL",
        "enable_llm": False,
    }
    res = client.post("/api/v1/reviews", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "review_id" in data
    assert data["file_path"] == "hello.py"
    assert data["quality_gate"]["status"] == GateStatus.PASS.value
    assert "execution_metadata" in data


def test_empty_code_submission_error():
    payload = {
        "code": "   ",
        "file_path": "empty.py",
    }
    res = client.post("/api/v1/reviews", json=payload)
    assert res.status_code == 422
    assert "Source code cannot be empty" in res.json()["detail"]


def test_invalid_request_schema():
    # Missing required 'code' field
    payload = {"file_path": "test.py"}
    res = client.post("/api/v1/reviews", json=payload)
    assert res.status_code == 422


def test_review_persistence_and_metrics():
    # Submit a review
    payload = {
        "code": "eval('1+1')\n",
        "file_path": "sec.py",
        "scope": "SECURITY",
    }
    res = client.post("/api/v1/reviews", json=payload)
    assert res.status_code == 201
    review_id = res.json()["review_id"]

    # Fetch by ID
    get_res = client.get(f"/api/v1/reviews/{review_id}")
    assert get_res.status_code == 200
    assert get_res.json()["review_id"] == review_id

    # List reviews
    list_res = client.get("/api/v1/reviews")
    assert list_res.status_code == 200
    assert any(r["review_id"] == review_id for r in list_res.json())

    # Check metrics
    metrics_res = client.get("/api/v1/reviews/metrics/summary")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_reviews"] >= 1
    assert "severity_distribution" in metrics


def test_get_nonexistent_review():
    res = client.get("/api/v1/reviews/non-existent-uuid-999")
    assert res.status_code == 404
