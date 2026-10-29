from typing import Dict, List, Optional

from app.config import settings
from app.schemas.review import (
    Finding,
    FindingCategory,
    FindingSeverity,
    GateStatus,
    QualityGateResult,
    QualityGateRuleConfig,
)


class QualityGateEvaluator:
    """Evaluates static and agent review findings against configurable quality gate rules."""

    def __init__(self, default_config: Optional[QualityGateRuleConfig] = None):
        self.config = default_config or QualityGateRuleConfig(
            block_on_critical=settings.GATE_BLOCK_ON_CRITICAL,
            block_on_high=settings.GATE_BLOCK_ON_HIGH,
            max_medium_allowed=settings.GATE_MAX_MEDIUM,
            max_low_allowed=settings.GATE_MAX_LOW,
        )

    def evaluate(
        self,
        findings: List[Finding],
        is_valid_syntax: bool = True,
        syntax_error: Optional[str] = None,
        analysis_error: Optional[str] = None,
        custom_config: Optional[QualityGateRuleConfig] = None,
        ai_review_ran: bool = False,
        semantic_retrieval_ran: bool = False,
    ) -> QualityGateResult:
        cfg = custom_config or self.config

        # 1. Handle Syntax & Analysis Errors
        if not is_valid_syntax or analysis_error:
            status = GateStatus.ERROR if syntax_error else GateStatus.INCOMPLETE
            summary = (
                f"Quality Gate {status.value}: Code analysis could not complete reliably "
                f"({syntax_error or analysis_error})."
            )
            blocking = [
                f for f in findings
                if f.category in (FindingCategory.SYNTAX, FindingCategory.ERROR)
            ]
            return QualityGateResult(
                status=status,
                summary=summary,
                blocking_findings=blocking,
                severity_counts={FindingSeverity.CRITICAL.value: len(blocking)},
                category_counts={FindingCategory.SYNTAX.value: len(blocking)},
                explanation=(
                    "The code contains syntax or execution errors preventing full AST analysis. "
                    "Address the syntax/parse errors before re-evaluating quality gates."
                ),
                ai_review_ran=ai_review_ran,
                semantic_retrieval_ran=semantic_retrieval_ran,
            )

        # 2. Count findings by severity and category
        severity_counts: Dict[str, int] = {s.value: 0 for s in FindingSeverity}
        category_counts: Dict[str, int] = {c.value: 0 for c in FindingCategory}

        for f in findings:
            s_val = f.severity.value
            c_val = f.category.value
            severity_counts[s_val] = severity_counts.get(s_val, 0) + 1
            category_counts[c_val] = category_counts.get(c_val, 0) + 1

        # 3. Determine blocking findings based on rule config
        blocking_findings: List[Finding] = []
        violations: List[str] = []

        critical_findings = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        high_findings = [f for f in findings if f.severity == FindingSeverity.HIGH]
        medium_findings = [f for f in findings if f.severity == FindingSeverity.MEDIUM]
        low_findings = [f for f in findings if f.severity == FindingSeverity.LOW]

        if cfg.block_on_critical and critical_findings:
            blocking_findings.extend(critical_findings)
            violations.append(f"{len(critical_findings)} Critical finding(s) detected (policy: 0 allowed)")

        if cfg.block_on_high and high_findings:
            blocking_findings.extend(high_findings)
            violations.append(f"{len(high_findings)} High-severity finding(s) detected (policy: 0 allowed)")

        if len(medium_findings) > cfg.max_medium_allowed:
            blocking_findings.extend(medium_findings)
            violations.append(
                f"{len(medium_findings)} Medium-severity findings exceeded threshold of {cfg.max_medium_allowed}"
            )

        if len(low_findings) > cfg.max_low_allowed:
            blocking_findings.extend(low_findings)
            violations.append(
                f"{len(low_findings)} Low-severity findings exceeded threshold of {cfg.max_low_allowed}"
            )

        # 4. Formulate Result
        if blocking_findings:
            status = GateStatus.FAIL
            summary = f"Quality Gate FAILED: {len(blocking_findings)} blocking issue(s) identified."
            explanation = "Quality gate blocked by the following policy triggers: " + "; ".join(violations) + "."
        else:
            status = GateStatus.PASS
            total = len(findings)
            summary = f"Quality Gate PASSED: {total} non-blocking finding(s) reported."
            explanation = (
                "All findings fall within acceptable thresholds defined by the quality gate policy. "
                f"Total issues: {total} (Medium: {len(medium_findings)}, Low: {len(low_findings)})."
            )

        return QualityGateResult(
            status=status,
            summary=summary,
            blocking_findings=blocking_findings,
            severity_counts=severity_counts,
            category_counts=category_counts,
            explanation=explanation,
            ai_review_ran=ai_review_ran,
            semantic_retrieval_ran=semantic_retrieval_ran,
        )


quality_gate_evaluator = QualityGateEvaluator()
