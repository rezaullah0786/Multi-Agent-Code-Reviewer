from app.schemas.review import (
    DetectionSource,
    Finding,
    FindingCategory,
    FindingSeverity,
    GateStatus,
    QualityGateRuleConfig,
)
from app.services.quality_gate import QualityGateEvaluator


def test_quality_gate_clean_pass():
    evaluator = QualityGateEvaluator()
    result = evaluator.evaluate(findings=[])
    assert result.status == GateStatus.PASS
    assert len(result.blocking_findings) == 0
    assert result.severity_counts[FindingSeverity.CRITICAL.value] == 0


def test_quality_gate_fail_critical():
    evaluator = QualityGateEvaluator()
    finding = Finding(
        rule_id="SEC001",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.CRITICAL,
        title="eval() usage",
        explanation="Dangerous dynamic execution",
        remediation="Avoid eval",
        line_number=5,
        source=DetectionSource.AST,
    )
    result = evaluator.evaluate(findings=[finding])
    assert result.status == GateStatus.FAIL
    assert len(result.blocking_findings) == 1
    assert "Critical finding(s) detected" in result.explanation


def test_quality_gate_fail_high():
    evaluator = QualityGateEvaluator()
    finding = Finding(
        rule_id="SEC004",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        title="Hardcoded API Key",
        explanation="Detected secret token in code",
        remediation="Use env variables",
        line_number=2,
        source=DetectionSource.AST,
    )
    result = evaluator.evaluate(findings=[finding])
    assert result.status == GateStatus.FAIL
    assert len(result.blocking_findings) == 1


def test_quality_gate_threshold_override():
    # If high is not blocking in custom config
    custom_cfg = QualityGateRuleConfig(block_on_critical=True, block_on_high=False)
    evaluator = QualityGateEvaluator()
    finding = Finding(
        rule_id="SEC004",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        title="Hardcoded API Key",
        explanation="Detected secret token in code",
        remediation="Use env variables",
        line_number=2,
        source=DetectionSource.AST,
    )
    result = evaluator.evaluate(findings=[finding], custom_config=custom_cfg)
    assert result.status == GateStatus.PASS


def test_quality_gate_syntax_error():
    evaluator = QualityGateEvaluator()
    result = evaluator.evaluate(
        findings=[],
        is_valid_syntax=False,
        syntax_error="unexpected EOF at line 12",
    )
    assert result.status == GateStatus.ERROR
    assert "unexpected EOF" in result.summary


def test_quality_gate_analysis_error():
    evaluator = QualityGateEvaluator()
    result = evaluator.evaluate(
        findings=[],
        is_valid_syntax=True,
        analysis_error="AST parse failed due to unknown encoding",
    )
    assert result.status == GateStatus.INCOMPLETE
    assert result.status == GateStatus.INCOMPLETE
