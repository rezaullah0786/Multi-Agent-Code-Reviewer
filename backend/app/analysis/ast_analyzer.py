import ast
from typing import List, Optional, Tuple

from app.analysis.performance_rules import PerformanceASTVisitor
from app.analysis.security_rules import SecurityASTVisitor
from app.analysis.style_rules import StyleASTVisitor
from app.schemas.review import (
    DetectionSource,
    Finding,
    FindingCategory,
    FindingSeverity,
    ReviewScope,
)


class ASTAnalyzer:
    """Deterministic static code analysis engine using Python Abstract Syntax Trees (AST)."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def analyze(
        self, code: str, scope: ReviewScope = ReviewScope.ALL
    ) -> Tuple[List[Finding], bool, Optional[str]]:
        """
        Analyzes source code using AST visitors.
        Returns:
            (findings, is_valid_syntax, syntax_error_message)
        """
        findings: List[Finding] = []
        code_lines = code.splitlines()

        # Handle empty code
        if not code.strip():
            return findings, True, None

        # Parse AST
        try:
            tree = ast.parse(code, filename=self.file_path or "<string>")
        except SyntaxError as e:
            err_line = e.lineno or 1
            snippet = code_lines[err_line - 1].strip() if 1 <= err_line <= len(code_lines) else None
            syntax_finding = Finding(
                rule_id="SYNTAX001",
                category=FindingCategory.SYNTAX,
                severity=FindingSeverity.CRITICAL,
                title="Python Syntax Error",
                explanation=f"Source code failed to parse: {e.msg} (offset: {e.offset})",
                remediation="Correct syntax error before continuing code review.",
                file_path=self.file_path,
                line_number=err_line,
                source=DetectionSource.AST,
                confidence=1.0,
                snippet=snippet,
            )
            return [syntax_finding], False, f"{e.msg} at line {err_line}"
        except Exception as e:
            error_finding = Finding(
                rule_id="PARSE_ERR",
                category=FindingCategory.ERROR,
                severity=FindingSeverity.CRITICAL,
                title="AST Parse Error",
                explanation=f"Unexpected error parsing source code: {str(e)}",
                remediation="Ensure code is valid UTF-8 formatted Python source code.",
                file_path=self.file_path,
                line_number=1,
                source=DetectionSource.AST,
                confidence=1.0,
            )
            return [error_finding], False, str(e)

        # Execute visitors based on review scope
        if scope in (ReviewScope.ALL, ReviewScope.SECURITY):
            sec_visitor = SecurityASTVisitor(code_lines, self.file_path)
            sec_visitor.visit(tree)
            findings.extend(sec_visitor.findings)

        if scope in (ReviewScope.ALL, ReviewScope.PERFORMANCE):
            perf_visitor = PerformanceASTVisitor(code_lines, self.file_path)
            perf_visitor.visit(tree)
            findings.extend(perf_visitor.findings)

        if scope in (ReviewScope.ALL, ReviewScope.STYLE):
            style_visitor = StyleASTVisitor(code_lines, self.file_path)
            style_visitor.visit(tree)
            findings.extend(style_visitor.findings)

        return findings, True, None
