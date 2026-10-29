import time
from typing import Any, Dict, List, Optional

from app.agents.performance_agent import performance_agent
from app.agents.security_agent import security_agent
from app.agents.shared import deduplicate_findings
from app.agents.style_agent import style_agent
from app.analysis.ast_analyzer import ASTAnalyzer
from app.retrieval.qdrant_store import qdrant_store
from app.schemas.review import (
    Finding,
    QualityGateRuleConfig,
    ReviewScope,
)
from app.services.llm_service import llm_service
from app.services.quality_gate import quality_gate_evaluator
from app.workflow.state import ReviewState


def ast_analysis_node(state: ReviewState) -> Dict[str, Any]:
    """Node 1: Executes deterministic AST-based static analysis."""
    code = state.get("code", "")
    file_path = state.get("file_path", "main.py")
    scope_str = state.get("scope", ReviewScope.ALL.value)
    scope = ReviewScope(scope_str) if scope_str in ReviewScope._value2member_map_ else ReviewScope.ALL

    analyzer = ASTAnalyzer(file_path=file_path)
    findings, is_valid_syntax, syntax_error = analyzer.analyze(code, scope=scope)

    return {
        "ast_findings": [f.model_dump() for f in findings],
        "is_valid_syntax": is_valid_syntax,
        "syntax_error": syntax_error,
        "analysis_error": None if is_valid_syntax else syntax_error,
    }


def retrieval_node(state: ReviewState) -> Dict[str, Any]:
    """Node 2: Queries Qdrant vector index for relevant repository context."""
    code = state.get("code", "")
    if not code.strip() or not qdrant_store.is_connected:
        return {"retrieved_context": None, "semantic_retrieval_ran": False}

    query_sample = "\n".join(code.splitlines()[:10])
    results = qdrant_store.search(query=query_sample, limit=3)

    if results:
        context_snippets = []
        for r in results:
            context_snippets.append(
                f"# File: {r.file_path} (Lines {r.start_line}-{r.end_line}, score: {r.score:.2f})\n{r.content}"
            )
        formatted_context = "\n---\n".join(context_snippets)
        return {
            "retrieved_context": formatted_context,
            "semantic_retrieval_ran": True,
        }

    return {"retrieved_context": None, "semantic_retrieval_ran": False}


def security_agent_node(state: ReviewState) -> Dict[str, Any]:
    """Node 3: Security Agent evaluation."""
    scope_str = state.get("scope", ReviewScope.ALL.value)
    enable_llm = state.get("enable_llm", False)
    is_valid_syntax = state.get("is_valid_syntax", True)

    if not is_valid_syntax or scope_str not in (ReviewScope.ALL.value, ReviewScope.SECURITY.value):
        return {"security_findings": []}

    code = state.get("code", "")
    file_path = state.get("file_path")
    context = state.get("retrieved_context")

    findings = security_agent.review(
        code=code,
        file_path=file_path,
        retrieved_context=context,
        enable_llm=enable_llm,
    )
    return {"security_findings": [f.model_dump() for f in findings]}


def performance_agent_node(state: ReviewState) -> Dict[str, Any]:
    """Node 4: Performance Agent evaluation."""
    scope_str = state.get("scope", ReviewScope.ALL.value)
    enable_llm = state.get("enable_llm", False)
    is_valid_syntax = state.get("is_valid_syntax", True)

    if not is_valid_syntax or scope_str not in (ReviewScope.ALL.value, ReviewScope.PERFORMANCE.value):
        return {"performance_findings": []}

    code = state.get("code", "")
    file_path = state.get("file_path")
    context = state.get("retrieved_context")

    findings = performance_agent.review(
        code=code,
        file_path=file_path,
        retrieved_context=context,
        enable_llm=enable_llm,
    )
    return {"performance_findings": [f.model_dump() for f in findings]}


def style_agent_node(state: ReviewState) -> Dict[str, Any]:
    """Node 5: Style & Maintainability Agent evaluation."""
    scope_str = state.get("scope", ReviewScope.ALL.value)
    enable_llm = state.get("enable_llm", False)
    is_valid_syntax = state.get("is_valid_syntax", True)

    if not is_valid_syntax or scope_str not in (ReviewScope.ALL.value, ReviewScope.STYLE.value):
        return {"style_findings": []}

    code = state.get("code", "")
    file_path = state.get("file_path")
    context = state.get("retrieved_context")

    findings = style_agent.review(
        code=code,
        file_path=file_path,
        retrieved_context=context,
        enable_llm=enable_llm,
    )
    return {"style_findings": [f.model_dump() for f in findings]}


def aggregator_validation_node(state: ReviewState) -> Dict[str, Any]:
    """Node 6: Combines findings, verifies Pydantic models, deduplicates, and evaluates Quality Gate."""
    code = state.get("code", "")
    raw_ast = state.get("ast_findings", [])
    raw_sec = state.get("security_findings", [])
    raw_perf = state.get("performance_findings", [])
    raw_style = state.get("style_findings", [])

    all_raw = raw_ast + raw_sec + raw_perf + raw_style

    validated_findings: List[Finding] = []
    code_lines_count = len(code.splitlines())

    for item in all_raw:
        try:
            finding = Finding.model_validate(item)
            # Guardrail: Validate line numbers against supplied source code
            if finding.line_number and finding.line_number > max(1, code_lines_count):
                finding.line_number = None
            validated_findings.append(finding)
        except Exception:
            continue

    # Deduplicate overlapping findings
    deduped = deduplicate_findings(validated_findings)

    # Custom quality gate configuration if provided
    custom_cfg = None
    if state.get("quality_gate_config"):
        try:
            custom_cfg = QualityGateRuleConfig.model_validate(state["quality_gate_config"])
        except Exception:
            pass

    ai_ran = bool(state.get("enable_llm") and llm_service.is_available())
    retrieval_ran = bool(state.get("semantic_retrieval_ran", False))

    qg_result = quality_gate_evaluator.evaluate(
        findings=deduped,
        is_valid_syntax=state.get("is_valid_syntax", True),
        syntax_error=state.get("syntax_error"),
        analysis_error=state.get("analysis_error"),
        custom_config=custom_cfg,
        ai_review_ran=ai_ran,
        semantic_retrieval_ran=retrieval_ran,
    )

    metadata = {
        "deterministic_ast_ran": True,
        "llm_agents_ran": ai_ran,
        "semantic_retrieval_ran": retrieval_ran,
        "qdrant_mode": qdrant_store.storage_mode,
        "agents_executed": ["ASTAnalyzer", "SecurityAgent", "PerformanceAgent", "StyleAgent"],
        "skipped_capabilities": (
            []
            if ai_ran
            else ["LLM-assisted deeper contextual reasoning (API key not configured or disabled)"]
        ),
    }

    return {
        "all_findings": [f.model_dump() for f in deduped],
        "quality_gate_result": qg_result.model_dump(),
        "execution_metadata": metadata,
    }
