from typing import Any, Dict
from fastapi import APIRouter

from app.config import settings
from app.retrieval.qdrant_store import qdrant_store
from app.services.llm_service import llm_service
from app.services.storage import storage

router = APIRouter(tags=["Health & Status"])


@router.get("/health", response_model=Dict[str, Any])
def get_health() -> Dict[str, Any]:
    """Provides overall system health, diagnostics, and component operational modes."""
    metrics = storage.get_metrics()
    llm_diag = llm_service.get_provider_status()
    qdrant_diag = qdrant_store.get_status()

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": "production" if llm_diag["is_configured"] else "local-demonstration",
        "components": {
            "ast_engine": {"status": "operational", "rules": "deterministic_python_ast"},
            "llm_provider": llm_diag,
            "vector_store": qdrant_diag,
            "database": {
                "status": "operational",
                "type": "sqlite",
                "total_records": metrics["total_reviews"],
            },
            "github_integration": {
                "dry_run_mode": settings.GITHUB_DRY_RUN,
                "webhook_secret_configured": bool(settings.GITHUB_WEBHOOK_SECRET),
                "github_token_configured": bool(settings.GITHUB_TOKEN),
            },
        },
    }
