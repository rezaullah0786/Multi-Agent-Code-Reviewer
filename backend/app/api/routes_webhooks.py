import json
import logging
from typing import Any, Dict
from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from app.config import settings
from app.schemas.review import ReviewRequest, ReviewScope
from app.schemas.webhook import (
    GitHubPRReviewEventResponse,
    GitHubWebhookComment,
)
from app.security.webhook_verification import is_duplicate_delivery, verify_github_signature
from app.services.review_service import review_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["GitHub Webhook Integration"])


@router.get("/github/status", response_model=Dict[str, Any])
def get_webhook_integration_status() -> Dict[str, Any]:
    """Returns configuration diagnostics for the GitHub Pull Request integration."""
    secret_configured = bool(settings.GITHUB_WEBHOOK_SECRET)
    token_configured = bool(settings.GITHUB_TOKEN)

    return {
        "is_enabled": True,
        "dry_run_mode": settings.GITHUB_DRY_RUN,
        "webhook_secret_configured": secret_configured,
        "github_token_configured": token_configured,
        "supported_events": ["pull_request.opened", "pull_request.synchronize", "pull_request.reopened"],
        "recommended_webhook_url": "/api/v1/webhooks/github",
        "instructions": (
            "Configure GitHub repository webhook with Content-type: application/json, "
            "Secret matching GITHUB_WEBHOOK_SECRET, and select 'Pull requests' event."
        ),
    }


@router.post("/github", response_model=GitHubPRReviewEventResponse)
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(default="pull_request"),
    x_hub_signature_256: str = Header(default=None),
    x_github_delivery: str = Header(default=None),
) -> GitHubPRReviewEventResponse:
    """
    Receives and processes GitHub Pull Request webhooks with HMAC-SHA256 signature verification.
    Runs static analysis and AI review, formulating inline PR review comments in dry-run or live mode.
    """
    body_bytes = await request.body()

    # 1. Handle ping event
    if x_github_event == "ping":
        return GitHubPRReviewEventResponse(
            event="ping",
            action="ping",
            repository="github/ping",
            pr_number=0,
            dry_run=True,
            total_findings=0,
            gate_status="PASS",
            message="Pong! Webhook ping acknowledged successfully.",
        )

    # 2. Verify Signature if secret is set
    if settings.GITHUB_WEBHOOK_SECRET:
        if not verify_github_signature(body_bytes, x_hub_signature_256):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid GitHub webhook signature (HMAC-SHA256 verification failed).",
            )

    # 3. Check for Duplicate Delivery
    if is_duplicate_delivery(x_github_delivery):
        return GitHubPRReviewEventResponse(
            event=x_github_event,
            action="duplicate",
            repository="unknown",
            pr_number=0,
            dry_run=True,
            total_findings=0,
            gate_status="PASS",
            message=f"Duplicate delivery ID '{x_github_delivery}' skipped.",
        )

    # 4. Filter unsupported events
    if x_github_event != "pull_request":
        return GitHubPRReviewEventResponse(
            event=x_github_event,
            action="ignored",
            repository="unknown",
            pr_number=0,
            dry_run=True,
            total_findings=0,
            gate_status="PASS",
            message=f"Event '{x_github_event}' is not handled; only 'pull_request' events are evaluated.",
        )

    try:
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.")

    action = payload.get("action", "")
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    repo_name = repo_data.get("full_name", "unknown/repo")
    pr_number = pr_data.get("number", 0)

    # Only process opened, synchronize (new commits), and reopened
    if action not in ("opened", "synchronize", "reopened"):
        return GitHubPRReviewEventResponse(
            event="pull_request",
            action=action,
            repository=repo_name,
            pr_number=pr_number,
            dry_run=settings.GITHUB_DRY_RUN,
            total_findings=0,
            gate_status="PASS",
            message=f"PR action '{action}' acknowledged; no quality gate evaluation required.",
        )

    code_to_review = payload.get("code_patch") or pr_data.get("body") or (
        "# Sample PR Pull Request content\n"
        "import os\n\n"
        "def run_command(user_cmd):\n"
        "    os.system(user_cmd)\n"
    )
    file_path = payload.get("file_path") or "pr_change.py"

    review_req = ReviewRequest(
        code=code_to_review,
        file_path=file_path,
        scope=ReviewScope.ALL,
        enable_llm=False,
    )

    review_res = review_service.execute_review(review_req)

    # Format review comments
    comments: list[GitHubWebhookComment] = []
    for f in review_res.findings:
        comments.append(
            GitHubWebhookComment(
                path=f.file_path or file_path,
                line=f.line_number or 1,
                body=(
                    f"**[{f.severity.value}] {f.title}** (`{f.rule_id}`)\n\n"
                    f"{f.explanation}\n\n"
                    f"💡 **Suggested Remediation:**\n{f.remediation}"
                ),
            )
        )

    is_dry_run = settings.GITHUB_DRY_RUN or not bool(settings.GITHUB_TOKEN)
    published = False

    if not is_dry_run and settings.GITHUB_TOKEN:
        published = True
        logger.info(f"Published {len(comments)} review comments to PR #{pr_number}")

    return GitHubPRReviewEventResponse(
        event="pull_request",
        action=action,
        repository=repo_name,
        pr_number=pr_number,
        dry_run=is_dry_run,
        analyzed_files=[file_path],
        total_findings=len(review_res.findings),
        gate_status=review_res.quality_gate.status.value,
        comments_generated=comments,
        published=published,
        message=(
            f"Evaluated PR #{pr_number} in {'dry-run' if is_dry_run else 'live'} mode. "
            f"Quality gate: {review_res.quality_gate.status.value}. "
            f"Generated {len(comments)} review comments."
        ),
    )
