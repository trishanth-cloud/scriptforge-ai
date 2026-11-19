"""
ScriptForge AI — Unit Tests for Code Validation Module
"""

import asyncio
from app.modules.code_validation import validate_script


def test_validate_python_valid():
    code = """
import sys

def add(a, b):
    return a + b

if __name__ == '__main__':
    print(add(2, 3))
"""
    result = asyncio.run(validate_script(code, "python"))
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_python_syntax_error():
    code = """
def bad_func(
    return 123
"""
    result = asyncio.run(validate_script(code, "python"))
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_validate_javascript_balanced_braces():
    valid_js = "function hello() { console.log('world'); }"
    result = asyncio.run(validate_script(valid_js, "javascript"))
    assert result.is_valid is True

    unbalanced = "function hello() { console.log('world');"
    result = asyncio.run(validate_script(unbalanced, "javascript"))
    assert result.is_valid is False


def test_validate_sql_syntax():
    valid_sql = "SELECT id, name FROM users WHERE active = 1;"
    result = asyncio.run(validate_script(valid_sql, "sql"))
    assert result.is_valid is True

    empty_sql = ""
    result = asyncio.run(validate_script(empty_sql, "sql"))
    assert result.is_valid is False
