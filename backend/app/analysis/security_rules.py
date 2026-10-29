import ast
import re
from typing import List, Optional

from app.schemas.review import DetectionSource, Finding, FindingCategory, FindingSeverity

# Patterns for hardcoded credential variable names
CREDENTIAL_VAR_REGEX = re.compile(
    r"(?i)(password|passwd|secret|api_key|apikey|access_token|auth_token|private_key|client_secret)"
)

# Common dummy strings that should not be flagged as real credentials
PLACEHOLDER_REGEX = re.compile(
    r"(?i)^(none|null|true|false|todo|placeholder|changeme|test|dummy|example|xxxx.*|<.*>|\${.*})$"
)

# SQL command keywords
SQL_KEYWORDS_REGEX = re.compile(
    r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|UNION)\b"
)


class SecurityASTVisitor(ast.NodeVisitor):
    def __init__(self, code_lines: List[str], file_path: Optional[str] = None):
        self.code_lines = code_lines
        self.file_path = file_path
        self.findings: List[Finding] = []

    def _get_snippet(self, lineno: Optional[int]) -> Optional[str]:
        if lineno and 1 <= lineno <= len(self.code_lines):
            return self.code_lines[lineno - 1].strip()
        return None

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._resolve_func_name(node.func)

        # SEC001: eval()
        if func_name == "eval":
            self.findings.append(
                Finding(
                    rule_id="SEC001",
                    category=FindingCategory.SECURITY,
                    severity=FindingSeverity.CRITICAL,
                    title="Unsafe dynamic execution via eval()",
                    explanation=(
                        "eval() parses and executes arbitrary Python expressions. "
                        "If any part of the input is influenced by external or untrusted data, "
                        "it allows Remote Code Execution (RCE)."
                    ),
                    remediation="Replace eval() with safe alternatives like ast.literal_eval() or explicit parsers.",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    source=DetectionSource.AST,
                    confidence=0.95,
                    snippet=self._get_snippet(node.lineno),
                )
            )

        # SEC002: exec()
        elif func_name == "exec":
            self.findings.append(
                Finding(
                    rule_id="SEC002",
                    category=FindingCategory.SECURITY,
                    severity=FindingSeverity.CRITICAL,
                    title="Unsafe dynamic execution via exec()",
                    explanation=(
                        "exec() dynamically executes arbitrary Python code statements. "
                        "Executing dynamically constructed or untrusted strings can lead to complete host compromise."
                    ),
                    remediation="Refactor the architecture to dispatch via functions or dictionaries instead of dynamic code execution.",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    source=DetectionSource.AST,
                    confidence=0.95,
                    snippet=self._get_snippet(node.lineno),
                )
            )

        # SEC003: Subprocess with shell=True or dangerous execution
        elif func_name in (
            "subprocess.Popen",
            "subprocess.run",
            "subprocess.call",
            "subprocess.check_call",
            "subprocess.check_output",
            "os.system",
            "os.popen",
        ):
            if func_name in ("os.system", "os.popen"):
                self.findings.append(
                    Finding(
                        rule_id="SEC003",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.HIGH,
                        title=f"Potentially dangerous process execution using {func_name}",
                        explanation=(
                            f"{func_name} runs commands through the system shell. "
                            "Unsanitized inputs easily lead to command injection."
                        ),
                        remediation="Use subprocess.run() with shell=False and pass arguments as a structured list.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        source=DetectionSource.AST,
                        confidence=0.9,
                        snippet=self._get_snippet(node.lineno),
                    )
                )
            else:
                # Check for shell=True
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.findings.append(
                            Finding(
                                rule_id="SEC003",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.CRITICAL,
                                title=f"Dangerous subprocess invocation with shell=True in {func_name}",
                                explanation=(
                                    "Calling subprocess functions with shell=True passes the command string directly "
                                    "to the system shell, exposing the application to shell command injection."
                                ),
                                remediation="Set shell=False and pass command and arguments as a list of strings.",
                                file_path=self.file_path,
                                line_number=node.lineno,
                                source=DetectionSource.AST,
                                confidence=0.95,
                                snippet=self._get_snippet(node.lineno),
                            )
                        )

        # SEC006: Insecure deserialization (pickle, yaml)
        elif func_name in ("pickle.loads", "pickle.load", "_pickle.loads", "_pickle.load"):
            self.findings.append(
                Finding(
                    rule_id="SEC006",
                    category=FindingCategory.SECURITY,
                    severity=FindingSeverity.HIGH,
                    title="Insecure deserialization using pickle",
                    explanation=(
                        "The pickle module is not secure against erroneous or maliciously constructed data. "
                        "Never unpickle data received from an untrusted or unauthenticated source."
                    ),
                    remediation="Use safe serialization formats like JSON, Protocol Buffers, or cryptographically signed tokens.",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    source=DetectionSource.AST,
                    confidence=0.85,
                    snippet=self._get_snippet(node.lineno),
                )
            )
        elif func_name == "yaml.load":
            # Check if Loader keyword argument is provided and safe
            has_safe_loader = any(
                kw.arg == "Loader" and "SafeLoader" in ast.dump(kw.value)
                for kw in node.keywords
            )
            if not has_safe_loader:
                self.findings.append(
                    Finding(
                        rule_id="SEC006",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.HIGH,
                        title="Unsafe YAML loading via yaml.load",
                        explanation="yaml.load() without SafeLoader can instantiate arbitrary Python objects.",
                        remediation="Use yaml.safe_load() or specify Loader=yaml.SafeLoader.",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        source=DetectionSource.AST,
                        confidence=0.9,
                        snippet=self._get_snippet(node.lineno),
                    )
                )

        # SEC007: Weak cryptography (MD5 / SHA1)
        elif func_name in ("hashlib.md5", "hashlib.sha1"):
            self.findings.append(
                Finding(
                    rule_id="SEC007",
                    category=FindingCategory.SECURITY,
                    severity=FindingSeverity.MEDIUM,
                    title=f"Use of cryptographically broken hash algorithm ({func_name})",
                    explanation=(
                        f"{func_name} is vulnerable to collision attacks and should not be used for security-sensitive purposes "
                        "(e.g., password hashing, HMAC, or signatures)."
                    ),
                    remediation="Use SHA-256 (hashlib.sha256) or modern password hashing algorithms like bcrypt/argon2.",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    source=DetectionSource.AST,
                    confidence=0.8,
                    snippet=self._get_snippet(node.lineno),
                )
            )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # SEC004: Hardcoded credential detection
        for target in node.targets:
            var_name = self._get_target_name(target)
            if var_name and CREDENTIAL_VAR_REGEX.search(var_name):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    val = node.value.value.strip()
                    # Filter out placeholders, empty strings, and template variables
                    if len(val) >= 4 and not PLACEHOLDER_REGEX.match(val):
                        self.findings.append(
                            Finding(
                                rule_id="SEC004",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.HIGH,
                                title=f"Potential hardcoded secret or credential in variable '{var_name}'",
                                explanation=(
                                    f"Variable '{var_name}' appears to store a hardcoded secret or token. "
                                    "Committing credentials into source code risks leakages and unauthorized access."
                                ),
                                remediation="Store credentials in environment variables or a secure secret manager (e.g., HashiCorp Vault).",
                                file_path=self.file_path,
                                line_number=node.lineno,
                                source=DetectionSource.AST,
                                confidence=0.85,
                                snippet=f"{var_name} = '********'",
                            )
                        )

        # SEC005: SQL query formatted via string concatenation or format
        self._check_sql_construction(node)

        self.generic_visit(node)

    def _check_sql_construction(self, node: ast.AST) -> None:
        # Check JoinedStr (f-strings) or BinOp (+) containing SQL keywords
        if isinstance(node, (ast.Assign, ast.Expr)):
            val = node.value if isinstance(node, ast.Assign) else node.value
            if isinstance(val, ast.JoinedStr):
                # Check if literal parts have SQL keywords
                raw_parts = [
                    part.value for part in val.values
                    if isinstance(part, ast.Constant) and isinstance(part.value, str)
                ]
                combined = " ".join(raw_parts)
                if SQL_KEYWORDS_REGEX.search(combined):
                    self.findings.append(
                        Finding(
                            rule_id="SEC005",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.HIGH,
                            title="Potential SQL injection via f-string dynamic construction",
                            explanation=(
                                "Constructing SQL queries using f-strings allows user-supplied variables "
                                "to alter query structure, resulting in SQL injection."
                            ),
                            remediation="Use parameterized queries with placeholders provided by your database driver or ORM.",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            source=DetectionSource.AST,
                            confidence=0.85,
                            snippet=self._get_snippet(node.lineno),
                        )
                    )
            elif isinstance(val, ast.BinOp) and isinstance(val.op, ast.Add):
                # String concatenation
                if self._contains_sql_string(val):
                    self.findings.append(
                        Finding(
                            rule_id="SEC005",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.HIGH,
                            title="Potential SQL injection via string concatenation (+)",
                            explanation=(
                                "Concatenating SQL query strings using '+' operator risks SQL injection if untrusted inputs are combined."
                            ),
                            remediation="Use parameterized queries provided by your database adapter (e.g., cursor.execute(query, params)).",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            source=DetectionSource.AST,
                            confidence=0.8,
                            snippet=self._get_snippet(node.lineno),
                        )
                    )

    def _contains_sql_string(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return bool(SQL_KEYWORDS_REGEX.search(node.value))
        if isinstance(node, ast.BinOp):
            return self._contains_sql_string(node.left) or self._contains_sql_string(node.right)
        return False

    def _resolve_func_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val_name = self._resolve_func_name(node.value)
            return f"{val_name}.{node.attr}" if val_name else node.attr
        return ""

    def _get_target_name(self, target: ast.AST) -> Optional[str]:
        if isinstance(target, ast.Name):
            return target.id
        elif isinstance(target, ast.Attribute):
            return target.attr
        return None
