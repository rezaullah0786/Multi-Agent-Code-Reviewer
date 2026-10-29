import hashlib
import hmac
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.security.webhook_verification import is_duplicate_delivery, verify_github_signature

client = TestClient(app)


def test_signature_verification_helper():
    original_secret = settings.GITHUB_WEBHOOK_SECRET
    settings.GITHUB_WEBHOOK_SECRET = "test_secret_key_123"

    payload = b'{"action": "opened"}'
    valid_sig = "sha256=" + hmac.new(
        b"test_secret_key_123", payload, hashlib.sha256
    ).hexdigest()

    assert verify_github_signature(payload, valid_sig) is True
    assert verify_github_signature(payload, "sha256=invalid_hash") is False
    assert verify_github_signature(payload, None) is False

    settings.GITHUB_WEBHOOK_SECRET = original_secret


def test_duplicate_delivery_detection():
    delivery_id = "test-uuid-delivery-999"
    # First delivery is not a duplicate
    assert is_duplicate_delivery(delivery_id) is False
    # Second delivery with same ID is detected as duplicate
    assert is_duplicate_delivery(delivery_id) is True


def test_webhook_ping_event():
    res = client.post(
        "/api/v1/webhooks/github",
        headers={"X-GitHub-Event": "ping"},
        json={"zen": "Design for failure."},
    )
    assert res.status_code == 200
    assert res.json()["action"] == "ping"
    assert "Pong" in res.json()["message"]


def test_webhook_pr_review_dry_run():
    payload = {
        "action": "opened",
        "repository": {"full_name": "enterprise/repo"},
        "pull_request": {"number": 42},
        "code_patch": "eval('dangerous_input')\n",
        "file_path": "security_test.py",
    }
    res = client.post(
        "/api/v1/webhooks/github",
        headers={
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "unique-delivery-uuid-001",
        },
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["pr_number"] == 42
    assert data["dry_run"] is True
    assert data["gate_status"] == "FAIL"
    assert len(data["comments_generated"]) >= 1
    assert "SEC001" in data["comments_generated"][0]["body"]
