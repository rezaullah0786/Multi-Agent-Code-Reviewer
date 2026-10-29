import ast
from typing import List, Optional, Set

from app.schemas.review import DetectionSource, Finding, FindingCategory, FindingSeverity


class PerformanceASTVisitor(ast.NodeVisitor):
    def __init__(self, code_lines: List[str], file_path: Optional[str] = None):
        self.code_lines = code_lines
        self.file_path = file_path
        self.findings: List[Finding] = []
        self.in_loop: int = 0
        self.in_async_func: bool = False
        self.with_context_open_lines: Set[int] = set()

    def _get_snippet(self, lineno: Optional[int]) -> Optional[str]:
        if lineno and 1 <= lineno <= len(self.code_lines):
            return self.code_lines[lineno - 1].strip()
        return None

    def visit_With(self, node: ast.With) -> None:
        # Track open() calls that are safely wrapped in `with`
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                func_name = self._resolve_func_name(item.context_expr.func)
                if func_name == "open":
                    self.with_context_open_lines.add(item.context_expr.lineno)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        prev_async = self.in_async_func
        self.in_async_func = True
        self.generic_visit(node)
        self.in_async_func = prev_async

    def visit_For(self, node: ast.For) -> None:
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1

    def visit_While(self, node: ast.While) -> None:
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        # PERF001: String concatenation in loop
        if self.in_loop > 0 and isinstance(node.op, ast.Add):
            # If the target or value is string-like or variable
            self.findings.append(
                Finding(
                    rule_id="PERF001",
                    category=FindingCategory.PERFORMANCE,
                    severity=FindingSeverity.MEDIUM,
                    title="Repeated string concatenation inside loop (+=",
                    explanation=(
                        "Repeated string concatenation in a loop creates new string copies at each iteration, "
                        "leading to O(N^2) memory and CPU overhead."
                    ),
                    remediation="Accumulate string parts in a list and join them with ''.join(parts) after the loop.",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    source=DetectionSource.AST,
                    confidence=0.8,
                    snippet=self._get_snippet(node.lineno),
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._resolve_func_name(node.func)

        # PERF003: open() called without context manager
        if func_name == "open":
            if node.lineno not in self.with_context_open_lines:
                self.findings.append(
                    Finding(
                        rule_id="PERF003",
                        category=FindingCategory.PERFORMANCE,
                        severity=FindingSeverity.LOW,
                        title="File opened without 'with' context manager",
                        explanation=(
                            "Opening a file without a context manager risks leaving the file descriptor open "
                            "if an exception or premature return occurs before close()."
                        ),
                        remediation="Use 'with open(...) as f:' to ensure automatic and prompt resource cleanup.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        source=DetectionSource.AST,
                        confidence=0.9,
                        snippet=self._get_snippet(node.lineno),
                    )
                )

        # PERF004: Expensive repeated compilation in loop
        if self.in_loop > 0 and func_name in ("re.compile", "re.search", "re.match"):
            if func_name == "re.compile":
                self.findings.append(
                    Finding(
                        rule_id="PERF004",
                        category=FindingCategory.PERFORMANCE,
                        severity=FindingSeverity.MEDIUM,
                        title="Regex compilation re.compile() executed inside loop",
                        explanation=(
                            "Compiling regular expressions inside a loop re-parses the pattern on every iteration, "
                            "incurring needless CPU cycles."
                        ),
                        remediation="Pre-compile the regular expression pattern once outside the loop.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        source=DetectionSource.AST,
                        confidence=0.9,
                        snippet=self._get_snippet(node.lineno),
                    )
                )

        # PERF005: Synchronous blocking call inside async function
        if self.in_async_func:
            if func_name in ("time.sleep", "requests.get", "requests.post", "requests.put", "requests.delete"):
                async_alt = "asyncio.sleep()" if func_name == "time.sleep" else "httpx.AsyncClient or aiohttp"
                self.findings.append(
                    Finding(
                        rule_id="PERF005",
                        category=FindingCategory.PERFORMANCE,
                        severity=FindingSeverity.HIGH,
                        title=f"Blocking call '{func_name}' in async function",
                        explanation=(
                            f"Calling synchronous blocking function '{func_name}' inside an asynchronous function blocks "
                            "the entire asyncio event loop, starving all concurrent tasks."
                        ),
                        remediation=f"Use asynchronous non-blocking counterpart such as {async_alt}.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        source=DetectionSource.AST,
                        confidence=0.95,
                        snippet=self._get_snippet(node.lineno),
                    )
                )

        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # PERF002: Inefficient membership check inside loop (x in [...])
        if self.in_loop > 0:
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, (ast.In, ast.NotIn)):
                    if isinstance(comparator, ast.List):
                        self.findings.append(
                            Finding(
                                rule_id="PERF002",
                                category=FindingCategory.PERFORMANCE,
                                severity=FindingSeverity.LOW,
                                title="Linear membership check 'in [list]' inside loop",
                                explanation=(
                                    "Testing membership against a list inside a loop requires O(N) linear scanning per iteration. "
                                    "Converting the container to a set provides O(1) average lookup time."
                                ),
                                remediation="Convert the collection to a set() or tuple/lookup dict before the loop.",
                                file_path=self.file_path,
                                line_number=node.lineno,
                                source=DetectionSource.AST,
                                confidence=0.85,
                                snippet=self._get_snippet(node.lineno),
                            )
                        )
        self.generic_visit(node)

    def _resolve_func_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val_name = self._resolve_func_name(node.value)
            return f"{val_name}.{node.attr}" if val_name else node.attr
        return ""
