import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.review import (
    Finding,
    FindingCategory,
    FindingSeverity,
    GateStatus,
    QualityGateResult,
    ReviewResponse,
    ReviewScope,
    ReviewSummary,
)


class ReviewStorage:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    file_path TEXT,
                    scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT,
                    findings_json TEXT NOT NULL,
                    quality_gate_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews (created_at DESC)")
            conn.commit()

    def save_review(self, review: ReviewResponse) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO reviews (
                    review_id, timestamp, file_path, scope, status,
                    summary, findings_json, quality_gate_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review.review_id,
                    review.timestamp,
                    review.file_path,
                    review.scope.value if isinstance(review.scope, ReviewScope) else str(review.scope),
                    review.quality_gate.status.value if isinstance(review.quality_gate.status, GateStatus) else str(review.quality_gate.status),
                    review.quality_gate.summary,
                    json.dumps([f.model_dump() for f in review.findings]),
                    json.dumps(review.quality_gate.model_dump()),
                    json.dumps(review.execution_metadata),
                    time.time(),
                ),
            )
            conn.commit()

    def get_review(self, review_id: str) -> Optional[ReviewResponse]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM reviews WHERE review_id = ?",
                (review_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            findings_data = json.loads(row["findings_json"])
            qg_data = json.loads(row["quality_gate_json"])
            metadata = json.loads(row["metadata_json"])

            findings = [Finding.model_validate(f) for f in findings_data]
            quality_gate = QualityGateResult.model_validate(qg_data)

            return ReviewResponse(
                review_id=row["review_id"],
                timestamp=row["timestamp"],
                file_path=row["file_path"],
                scope=ReviewScope(row["scope"]),
                findings=findings,
                quality_gate=quality_gate,
                execution_metadata=metadata,
            )

    def list_reviews(self, limit: int = 50, offset: int = 0) -> List[ReviewSummary]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT review_id, timestamp, file_path, scope, status, findings_json
                FROM reviews
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = cursor.fetchall()
            summaries: List[ReviewSummary] = []
            for row in rows:
                findings_data = json.loads(row["findings_json"])
                critical = sum(1 for f in findings_data if f.get("severity") == FindingSeverity.CRITICAL.value)
                high = sum(1 for f in findings_data if f.get("severity") == FindingSeverity.HIGH.value)
                medium = sum(1 for f in findings_data if f.get("severity") == FindingSeverity.MEDIUM.value)
                low = sum(1 for f in findings_data if f.get("severity") == FindingSeverity.LOW.value)

                summaries.append(
                    ReviewSummary(
                        review_id=row["review_id"],
                        timestamp=row["timestamp"],
                        file_path=row["file_path"],
                        scope=ReviewScope(row["scope"]),
                        status=GateStatus(row["status"]),
                        total_findings=len(findings_data),
                        critical_count=critical,
                        high_count=high,
                        medium_count=medium,
                        low_count=low,
                    )
                )
            return summaries

    def get_metrics(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            total_cursor = conn.execute("SELECT COUNT(*) FROM reviews")
            total = total_cursor.fetchone()[0]

            status_cursor = conn.execute("SELECT status, COUNT(*) FROM reviews GROUP BY status")
            status_counts = {row[0]: row[1] for row in status_cursor.fetchall()}

            # Aggregate findings across reviews
            findings_cursor = conn.execute("SELECT findings_json FROM reviews")
            severity_counts = {s.value: 0 for s in FindingSeverity}
            category_counts = {c.value: 0 for c in FindingCategory}

            for row in findings_cursor.fetchall():
                findings_list = json.loads(row[0])
                for f in findings_list:
                    sev = f.get("severity")
                    cat = f.get("category")
                    if sev in severity_counts:
                        severity_counts[sev] += 1
                    if cat in category_counts:
                        category_counts[cat] += 1

            return {
                "total_reviews": total,
                "passed_gates": status_counts.get(GateStatus.PASS.value, 0),
                "failed_gates": status_counts.get(GateStatus.FAIL.value, 0),
                "incomplete_gates": status_counts.get(GateStatus.INCOMPLETE.value, 0),
                "error_gates": status_counts.get(GateStatus.ERROR.value, 0),
                "severity_distribution": severity_counts,
                "category_distribution": category_counts,
            }


storage = ReviewStorage()
