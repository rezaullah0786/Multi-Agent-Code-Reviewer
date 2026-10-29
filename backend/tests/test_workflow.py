from app.workflow.graph import run_review_workflow
from app.schemas.review import GateStatus, ReviewScope


def test_langgraph_workflow_execution_without_llm():
    code = """
import os

def test_fn(x):
    os.system(x)
"""
    initial_state = {
        "code": code,
        "file_path": "test.py",
        "scope": ReviewScope.ALL.value,
        "enable_llm": False,
    }
    result = run_review_workflow(initial_state)

    assert "ast_findings" in result
    assert "all_findings" in result
    assert "quality_gate_result" in result
    assert "execution_metadata" in result

    # Check that deterministic AST ran
    assert result["is_valid_syntax"] is True
    assert len(result["all_findings"]) > 0

    # Verify quality gate
    qg = result["quality_gate_result"]
    assert qg["status"] in (GateStatus.PASS.value, GateStatus.FAIL.value)
    assert qg["ai_review_ran"] is False

    # Verify execution metadata
    meta = result["execution_metadata"]
    assert meta["deterministic_ast_ran"] is True
    assert meta["llm_agents_ran"] is False
    assert "ASTAnalyzer" in meta["agents_executed"]


def test_langgraph_workflow_invalid_syntax():
    initial_state = {
        "code": "def faulty_syntax(:",
        "file_path": "faulty.py",
        "scope": ReviewScope.ALL.value,
        "enable_llm": False,
    }
    result = run_review_workflow(initial_state)

    assert result["is_valid_syntax"] is False
    assert result["syntax_error"] is not None
    assert result["quality_gate_result"]["status"] == GateStatus.ERROR.value
    assert len(result["all_findings"]) == 1
    assert result["all_findings"][0]["rule_id"] == "SYNTAX001"
