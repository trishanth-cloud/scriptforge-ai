"""
ScriptForge AI — Code Validation Module
Syntax validation for multiple languages.
"""

import ast
import logging
import re

from app.models.schemas import ValidationResult

logger = logging.getLogger(__name__)


async def validate_script(script: str, language: str) -> ValidationResult:
    """
    Validate script syntax for the given language.
    Returns a ValidationResult with errors, warnings, and suggestions.
    """
    language = language.lower().replace("-", "_")
    validators = {
        "python": _validate_python,
        "javascript": _validate_javascript,
        "typescript": _validate_javascript,  # basic JS checks apply
        "bash": _validate_bash,
        "powershell": _validate_powershell,
        "sql": _validate_sql,
        "html_css": _validate_html,
        "html": _validate_html,
    }
    validator = validators.get(language, _validate_generic)
    return validator(script)


# ── Python ──────────────────────────────────────────────────────


def _validate_python(script: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    # Compile check
    try:
        compile(script, "<script>", "exec")
    except SyntaxError as exc:
        errors.append(f"SyntaxError at line {exc.lineno}: {exc.msg}")

    # AST parse for deeper analysis
    try:
        tree = ast.parse(script)
        # Check for bare excepts
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                warnings.append(f"Bare 'except:' at line {node.lineno} — consider catching specific exceptions")
        # Check for `eval` / `exec` usage
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                    warnings.append(f"Use of '{func.id}()' at line {node.lineno} — potential security risk")
    except SyntaxError:
        pass  # already captured above

    if not errors:
        suggestions.append("Python syntax is valid.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
    )


# ── JavaScript / TypeScript ─────────────────────────────────────


def _validate_javascript(script: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    # Balanced braces / parens / brackets
    _check_balanced(script, errors)

    # Common mistakes
    if re.search(r"\bvar\b", script):
        warnings.append("Consider using 'let' or 'const' instead of 'var'.")

    if "console.log" in script:
        suggestions.append("Remember to remove console.log statements in production code.")

    if not errors:
        suggestions.append("Basic JavaScript syntax checks passed.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
    )


# ── Bash ────────────────────────────────────────────────────────


def _validate_bash(script: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    lines = script.splitlines()

    # Check shebang
    if lines and not lines[0].startswith("#!"):
        suggestions.append("Consider adding a shebang line (e.g., #!/usr/bin/env bash).")

    # Check balanced quotes
    _check_quotes(script, errors)

    # Basic keyword matching
    openers = sum(1 for l in lines if re.match(r"^\s*(if|for|while|until|case)\b", l))
    closers = sum(1 for l in lines if re.match(r"^\s*(fi|done|esac)\b", l))
    if openers > closers:
        warnings.append("Possible unclosed control structure (if/for/while).")

    if not errors:
        suggestions.append("Basic Bash syntax checks passed.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
    )


# ── PowerShell ──────────────────────────────────────────────────


def _validate_powershell(script: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    _check_balanced(script, errors)
    _check_quotes(script, errors)

    if not errors:
        suggestions.append("Basic PowerShell syntax checks passed.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
    )


# ── SQL ─────────────────────────────────────────────────────────


def _validate_sql(script: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    upper = script.upper()
    sql_keywords = {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "BEGIN", "COMMIT"}
    has_keyword = any(kw in upper for kw in sql_keywords)
    if not has_keyword:
        errors.append("No recognisable SQL keyword found.")

    # Warn about destructive operations
    for dangerous in ("DROP", "TRUNCATE", "DELETE"):
        if dangerous in upper:
            warnings.append(f"Script contains '{dangerous}' — verify this is intentional.")

    if not errors:
        suggestions.append("Basic SQL keyword validation passed.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
    )


# ── HTML ────────────────────────────────────────────────────────


def _validate_html(script: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    # Basic tag matching
    open_tags = re.findall(r"<(\w+)[\s>]", script)
    close_tags = re.findall(r"</(\w+)\s*>", script)

    void_elements = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed", "source", "track", "wbr"}
    open_non_void = [t.lower() for t in open_tags if t.lower() not in void_elements]
    close_lower = [t.lower() for t in close_tags]

    if len(open_non_void) > len(close_lower) + 2:
        warnings.append("Possible unclosed HTML tags.")
    elif len(close_lower) > len(open_non_void) + 2:
        warnings.append("More closing tags than opening tags detected.")

    if not errors:
        suggestions.append("Basic HTML structure checks passed.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        suggestions=suggestions,
    )


# ── Generic ─────────────────────────────────────────────────────


def _validate_generic(script: str) -> ValidationResult:
    return ValidationResult(
        is_valid=True,
        warnings=["No specific validator for this language; only basic checks applied."],
        suggestions=["Review the script manually."],
    )


# ── Helpers ─────────────────────────────────────────────────────


def _check_balanced(script: str, errors: list[str]) -> None:
    """Check balanced braces, parens, and brackets."""
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    in_string = False
    string_char = ""

    for i, ch in enumerate(script):
        if in_string:
            if ch == string_char and (i == 0 or script[i - 1] != "\\"):
                in_string = False
            continue
        if ch in ("'", '"', "`"):
            in_string = True
            string_char = ch
            continue
        if ch in ("(", "[", "{"):
            stack.append(ch)
        elif ch in (")", "]", "}"):
            if not stack or stack[-1] != pairs[ch]:
                errors.append(f"Unmatched '{ch}' near character {i}.")
                return
            stack.pop()

    if stack:
        errors.append(f"Unclosed '{stack[-1]}' — expected matching close.")


def _check_quotes(script: str, errors: list[str]) -> None:
    """Check for obviously unbalanced quotes."""
    for q in ('"', "'"):
        # Count occurrences outside of escaped contexts (rough check)
        count = script.count(q) - script.count(f"\\{q}")
        if count % 2 != 0:
            errors.append(f"Possibly unbalanced {q} quotes.")
