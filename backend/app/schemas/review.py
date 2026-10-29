from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, field_validator


class FindingCategory(str, Enum):
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    STYLE = "STYLE"
    SYNTAX = "SYNTAX"
    ERROR = "ERROR"


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ReviewScope(str, Enum):
    ALL = "ALL"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    STYLE = "STYLE"


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"
    ERROR = "ERROR"


class DetectionSource(str, Enum):
    AST = "AST"
    DETERMINISTIC_RULE = "DETERMINISTIC_RULE"
    SECURITY_AGENT = "SECURITY_AGENT"
    PERFORMANCE_AGENT = "PERFORMANCE_AGENT"
    STYLE_AGENT = "STYLE_AGENT"
    LLM = "LLM"


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = Field(..., description="Unique rule code, e.g., SEC001, PERF002, STY003")
    category: FindingCategory
    severity: FindingSeverity
    title: str = Field(..., min_length=3, max_length=150)
    explanation: str = Field(..., min_length=5)
    remediation: str = Field(..., min_length=5)
    file_path: Optional[str] = None
    line_number: Optional[int] = Field(default=None, description="1-indexed line number in source code")
    end_line_number: Optional[int] = None
    source: DetectionSource = DetectionSource.AST
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    snippet: Optional[str] = None

    @field_validator("line_number", "end_line_number")
    @classmethod
    def validate_positive_line(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("Line numbers must be 1-indexed positive integers")
        return v

    def validate_against_code(self, code: str) -> bool:
        """Verify that line number falls within actual code line count."""
        if not self.line_number:
            return True
        total_lines = len(code.splitlines())
        return self.line_number <= max(1, total_lines)


class QualityGateRuleConfig(BaseModel):
    block_on_critical: bool = Field(default=True, description="Fail gate if any critical findings exist")
    block_on_high: bool = Field(default=True, description="Fail gate if any high severity findings exist")
    max_medium_allowed: int = Field(default=5, ge=0, description="Max allowed medium findings before failure")
    max_low_allowed: int = Field(default=15, ge=0, description="Max allowed low findings before failure")


class QualityGateResult(BaseModel):
    status: GateStatus
    summary: str
    blocking_findings: List[Finding] = Field(default_factory=list)
    severity_counts: Dict[str, int] = Field(default_factory=dict)
    category_counts: Dict[str, int] = Field(default_factory=dict)
    explanation: str
    ai_review_ran: bool = False
    semantic_retrieval_ran: bool = False
    disclaimer: str = (
        "Passing the automated quality gate does not prove the code is free of defects. "
        "Automated gates provide structural checks and risk indicators."
    )


class ReviewRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=200000, description="Source code to inspect")
    file_path: Optional[str] = Field(default="main.py", description="Optional file path or name")
    scope: ReviewScope = Field(default=ReviewScope.ALL, description="Review scope selector")
    enable_llm: bool = Field(default=False, description="Whether to invoke LLM-assisted agent evaluation")
    quality_gate_config: Optional[QualityGateRuleConfig] = Field(
        default=None, description="Custom quality gate thresholds"
    )


class ReviewSummary(BaseModel):
    review_id: str
    timestamp: str
    file_path: Optional[str] = None
    scope: ReviewScope
    status: GateStatus
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


class ReviewResponse(BaseModel):
    review_id: str
    timestamp: str
    file_path: Optional[str] = None
    scope: ReviewScope
    findings: List[Finding] = Field(default_factory=list)
    quality_gate: QualityGateResult
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
