from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class ReviewState(TypedDict, total=False):
    # Inputs
    code: str
    file_path: Optional[str]
    scope: str
    enable_llm: bool
    quality_gate_config: Optional[Dict[str, Any]]

    # Static AST Analysis Results
    ast_findings: List[Dict[str, Any]]
    is_valid_syntax: bool
    syntax_error: Optional[str]
    analysis_error: Optional[str]

    # Retrieval Context
    retrieved_context: Optional[str]
    semantic_retrieval_ran: bool

    # Agent Findings
    security_findings: List[Dict[str, Any]]
    performance_findings: List[Dict[str, Any]]
    style_findings: List[Dict[str, Any]]

    # Combined & Validated Outputs
    all_findings: List[Dict[str, Any]]
    quality_gate_result: Optional[Dict[str, Any]]
    execution_metadata: Dict[str, Any]
