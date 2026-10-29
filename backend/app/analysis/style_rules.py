import ast
import re
from typing import List, Optional

from app.schemas.review import DetectionSource, Finding, FindingCategory, FindingSeverity

SNAKE_CASE_REGEX = re.compile(r"^[a-z_][a-z0-9_]*$")


class StyleASTVisitor(ast.NodeVisitor):
    def __init__(self, code_lines: List[str], file_path: Optional[str] = None):
        self.code_lines = code_lines
        self.file_path = file_path
        self.findings: List[Finding] = []

    def _get_snippet(self, lineno: Optional[int]) -> Optional[str]:
        if lineno and 1 <= lineno <= len(self.code_lines):
            return self.code_lines[lineno - 1].strip()
        return None

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        # STY001: Broad exception handling
        is_bare = node.type is None
        is_broad = False

        if node.type is not None:
            if isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException"):
                is_broad = True

        if is_bare or is_broad:
            # Check if body is just pass or empty
            is_silent = False
            if len(node.body) == 1:
                stmt = node.body[0]
                if isinstance(stmt, ast.Pass):
                    is_silent = True
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                    # Docstring/pass equivalent
                    is_silent = True

            severity = FindingSeverity.MEDIUM if is_silent else FindingSeverity.LOW
            handler_type = "Bare 'except:'" if is_bare else f"Broad 'except {node.type.id}:'"  # type: ignore
            title = f"{handler_type} catch block" + (" silently suppressing errors" if is_silent else "")

            self.findings.append(
                Finding(
                    rule_id="STY001",
                    category=FindingCategory.STYLE,
                    severity=severity,
                    title=title,
                    explanation=(
                        f"{handler_type} intercepts all exceptions indiscriminately, potentially masking critical bugs, "
                        "syntax errors, system interrupts, or memory issues."
                    ),
                    remediation="Catch specific, expected exception classes and log or handle the caught error appropriately.",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    source=DetectionSource.AST,
                    confidence=0.9,
                    snippet=self._get_snippet(node.lineno),
                )
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node: ast.AST) -> None:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        name = node.name
        # Skip dunder methods
        if not (name.startswith("__") and name.endswith("__")):
            # STY005: Snake case naming
            if not SNAKE_CASE_REGEX.match(name):
                self.findings.append(
                    Finding(
                        rule_id="STY005",
                        category=FindingCategory.STYLE,
                        severity=FindingSeverity.LOW,
                        title=f"Function '{name}' does not adhere to snake_case naming convention",
                        explanation="PEP 8 recommends snake_case formatting for Python function and method names.",
                        remediation=f"Rename '{name}' to follow lowercase snake_case conventions.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        source=DetectionSource.AST,
                        confidence=0.9,
                        snippet=self._get_snippet(node.lineno),
                    )
                )

        # STY002: Mutable default arguments
        defaults = node.args.defaults + node.args.kw_defaults
        for default in defaults:
            if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append(
                    Finding(
                        rule_id="STY002",
                        category=FindingCategory.STYLE,
                        severity=FindingSeverity.HIGH,
                        title=f"Mutable default argument in function '{name}'",
                        explanation=(
                            "Default argument values in Python are evaluated once at function definition time. "
                            "A mutable default (like list, dict, or set) persists state across calls, causing unintended bugs."
                        ),
                        remediation="Use 'None' as the default argument value and initialize the mutable object inside the function body.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        source=DetectionSource.AST,
                        confidence=0.95,
                        snippet=self._get_snippet(node.lineno),
                    )
                )

        # STY003: Too many arguments (> 6)
        total_args = (
            len(node.args.args)
            + len(node.args.kwonlyargs)
            + (1 if node.args.vararg else 0)
            + (1 if node.args.kwarg else 0)
        )
        # Deduct 'self' or 'cls' if first arg
        if node.args.args and node.args.args[0].arg in ("self", "cls"):
            total_args -= 1

        if total_args > 6:
            self.findings.append(
                Finding(
                    rule_id="STY003",
                    category=FindingCategory.STYLE,
                    severity=FindingSeverity.MEDIUM,
                    title=f"Function '{name}' has too many parameters ({total_args} > 6)",
                    explanation="Functions with many parameters are difficult to read, test, and maintain.",
                    remediation="Group related parameters into a dataclass, Pydantic model, or configuration dictionary.",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    source=DetectionSource.AST,
                    confidence=0.85,
                    snippet=self._get_snippet(node.lineno),
                )
            )

        # STY004: Overly long function (> 60 lines)
        if hasattr(node, "end_lineno") and node.end_lineno:
            func_len = node.end_lineno - node.lineno + 1
            if func_len > 60:
                self.findings.append(
                    Finding(
                        rule_id="STY004",
                        category=FindingCategory.STYLE,
                        severity=FindingSeverity.LOW,
                        title=f"Function '{name}' is overly long ({func_len} lines > 60)",
                        explanation="Overly long functions often violate the Single Responsibility Principle and increase cognitive load.",
                        remediation="Break down the function into smaller, well-scoped helper functions.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        end_line_number=node.end_lineno,
                        source=DetectionSource.AST,
                        confidence=0.8,
                        snippet=self._get_snippet(node.lineno),
                    )
                )
