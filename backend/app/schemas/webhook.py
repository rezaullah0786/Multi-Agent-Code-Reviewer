from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GitHubWebhookComment(BaseModel):
    path: str
    line: int
    body: str


class GitHubPRReviewEventResponse(BaseModel):
    event: str
    action: str
    repository: str
    pr_number: int
    dry_run: bool
    analyzed_files: List[str] = Field(default_factory=list)
    total_findings: int
    gate_status: str
    comments_generated: List[GitHubWebhookComment] = Field(default_factory=list)
    published: bool = False
    message: str


class GitHubWebhookVerificationResult(BaseModel):
    is_valid: bool
    event_type: Optional[str] = None
    delivery_id: Optional[str] = None
    reason: Optional[str] = None
