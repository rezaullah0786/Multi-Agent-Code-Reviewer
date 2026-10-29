from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.review import (
    ReviewRequest,
    ReviewResponse,
    ReviewSummary,
)
from app.services.review_service import review_service
from app.services.storage import storage

router = APIRouter(prefix="/reviews", tags=["Code Reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_code_review(request: ReviewRequest) -> ReviewResponse:
    """Submits Python source code for multi-agent AST and AI-assisted code review."""
    if not request.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source code cannot be empty.",
        )
    try:
        response = review_service.execute_review(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review execution failed: {str(e)}",
        )


@router.get("/metrics/summary", response_model=Dict[str, Any])
def get_dashboard_metrics() -> Dict[str, Any]:
    """Returns aggregated review statistics, quality gate pass/fail rates, and severity counts."""
    return storage.get_metrics()


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review_by_id(review_id: str) -> ReviewResponse:
    """Retrieves full details and findings for a past code review."""
    result = storage.get_review(review_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID '{review_id}' was not found.",
        )
    return result


@router.get("", response_model=List[ReviewSummary])
def list_code_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> List[ReviewSummary]:
    """Lists past code reviews with summary metrics and pagination."""
    return storage.list_reviews(limit=limit, offset=offset)
