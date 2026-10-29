import pytest
from app.analysis.ast_analyzer import ASTAnalyzer
from app.schemas.review import (
    FindingCategory,
    FindingSeverity,
    ReviewScope,
)


def test_empty_code_submission():
    analyzer = ASTAnalyzer()
    findings, is_valid, err = analyzer.analyze("")
    assert is_valid is True
    assert err is None
    assert len(findings) == 0


def test_syntax_error_handling():
    analyzer = ASTAnalyzer(file_path="syntax_fail.py")
    code = "def broken_func(:\n    return 42"
    findings, is_valid, err = analyzer.analyze(code)
    assert is_valid is False
    assert err is not None
    assert len(findings) == 1
    assert findings[0].rule_id == "SYNTAX001"
    assert findings[0].category == FindingCategory.SYNTAX
    assert findings[0].severity == FindingSeverity.CRITICAL
    assert findings[0].line_number == 1


def test_security_rules_eval_and_exec():
    analyzer = ASTAnalyzer()
    code = """
def run_dynamic(user_input):
    eval(user_input)
    exec(user_input)
"""
    findings, is_valid, err = analyzer.analyze(code, scope=ReviewScope.SECURITY)
    assert is_valid is True
    rule_ids = [f.rule_id for f in findings]
    assert "SEC001" in rule_ids
    assert "SEC002" in rule_ids
    assert all(f.category == FindingCategory.SECURITY for f in findings)


def test_security_rules_subprocess_shell_true():
    analyzer = ASTAnalyzer()
    code = """
import subprocess
import os

def run_cmd(user_cmd):
    subprocess.run("ls -la " + user_cmd, shell=True)
    os.system("echo " + user_cmd)
"""
    findings, is_valid, err = analyzer.analyze(code, scope=ReviewScope.SECURITY)
    assert is_valid is True
    rule_ids = [f.rule_id for f in findings]
    assert "SEC003" in rule_ids


def test_security_rules_hardcoded_secrets():
    analyzer = ASTAnalyzer()
    code = """
api_key = "sk-live-93821038102938109238"
client_secret = "super_secret_production_key"
"""
    findings, is_valid, err = analyzer.analyze(code, scope=ReviewScope.SECURITY)
    assert is_valid is True
    rule_ids = [f.rule_id for f in findings]
    assert "SEC004" in rule_ids
    assert any("sk-live" not in (f.snippet or "") for f in findings)  # Masked in snippet


def test_security_rules_sql_injection():
    analyzer = ASTAnalyzer()
    code = """
def get_user(user_id):
    query1 = f"SELECT * FROM users WHERE id = {user_id}"
    query2 = "SELECT * FROM accounts WHERE id = " + user_id
"""
    findings, is_valid, err = analyzer.analyze(code, scope=ReviewScope.SECURITY)
    assert is_valid is True
    sec005_findings = [f for f in findings if f.rule_id == "SEC005"]
    assert len(sec005_findings) >= 2


def test_performance_rules():
    analyzer = ASTAnalyzer()
    code = """
import time
import re

async def process_items(items):
    out = ""
    for item in items:
        out += str(item)
        if item in [1, 2, 3]:
            pass
        pattern = re.compile(r"\\d+")
    f = open("log.txt")
    time.sleep(1)
"""
    findings, is_valid, err = analyzer.analyze(code, scope=ReviewScope.PERFORMANCE)
    assert is_valid is True
    rule_ids = [f.rule_id for f in findings]
    assert "PERF001" in rule_ids  # string concat in loop
    assert "PERF002" in rule_ids  # membership in list
    assert "PERF003" in rule_ids  # unclosed open()
    assert "PERF004" in rule_ids  # re.compile in loop
    assert "PERF005" in rule_ids  # sync blocking time.sleep in async def


def test_style_rules():
    analyzer = ASTAnalyzer()
    code = """
def badFunctionStyle(a, b, c, d, e, f, g, h=[]):
    try:
        x = 10
    except:
        pass
"""
    findings, is_valid, err = analyzer.analyze(code, scope=ReviewScope.STYLE)
    assert is_valid is True
    rule_ids = [f.rule_id for f in findings]
    assert "STY001" in rule_ids  # bare except with pass
    assert "STY002" in rule_ids  # mutable default argument h=[]
    assert "STY003" in rule_ids  # too many parameters (> 6)
    assert "STY005" in rule_ids  # non-snake_case function name
