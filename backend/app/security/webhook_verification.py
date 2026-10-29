import hashlib
import hmac
from typing import Optional, Set

from app.config import settings

# Bounded delivery cache to prevent duplicate replay processing
PROCESSED_DELIVERIES: Set[str] = set()
MAX_DELIVERY_CACHE_SIZE = 1000


def verify_github_signature(payload_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Verifies that the webhook payload was sent by GitHub by validating
    the HMAC SHA-256 signature against the configured secret.
    """
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        # If no secret is configured, reject for security unless explicitly testing
        return False

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = "sha256=" + hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)


def is_duplicate_delivery(delivery_id: Optional[str]) -> bool:
    """Checks and records delivery id to avoid duplicate processing."""
    if not delivery_id:
        return False

    if delivery_id in PROCESSED_DELIVERIES:
        return True

    if len(PROCESSED_DELIVERIES) >= MAX_DELIVERY_CACHE_SIZE:
        PROCESSED_DELIVERIES.clear()

    PROCESSED_DELIVERIES.add(delivery_id)
    return False
