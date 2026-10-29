from datetime import datetime, timezone
import time
import uuid
from typing import Any, Dict

from app.schemas.review import (
    Finding,
    QualityGateResult,
    ReviewRequest,
    ReviewResponse,
    ReviewScope,
)
from app.services.storage import storage
from app.workflow.graph import run_review_workflow


class ReviewService:
    """Orchestrates code reviews via the LangGraph workflow and handles persistence."""

    def execute_review(self, request: ReviewRequest) -> ReviewResponse:
        review_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        start_time = time.perf_counter()

        initial_state = {
            "code": request.code,
            "file_path": request.file_path or "main.py",
            "scope": request.scope.value if isinstance(request.scope, ReviewScope) else str(request.scope),
            "enable_llm": request.enable_llm,
            "quality_gate_config": request.quality_gate_config.model_dump() if request.quality_gate_config else None,
        }

        # Run LangGraph workflow
        final_state: Dict[str, Any] = run_review_workflow(initial_state)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Deserialize validated findings and quality gate result
        findings = [Finding.model_validate(f) for f in final_state.get("all_findings", [])]
        qg_data = final_state.get("quality_gate_result", {})
        quality_gate = QualityGateResult.model_validate(qg_data)

        metadata = final_state.get("execution_metadata", {})
        metadata["duration_ms"] = duration_ms

        response = ReviewResponse(
            review_id=review_id,
            timestamp=timestamp,
            file_path=request.file_path,
            scope=request.scope,
            findings=findings,
            quality_gate=quality_gate,
            execution_metadata=metadata,
        )

        # Persist review for dashboard history and metrics
        storage.save_review(response)

        return response


review_service = ReviewService()
