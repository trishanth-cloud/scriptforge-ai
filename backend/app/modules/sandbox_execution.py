"""
ScriptForge AI — Sandbox Execution Module
Run generated scripts in isolated subprocesses.
"""

import asyncio
import logging
import sqlite3
import tempfile
import time
from pathlib import Path

import sys
from app.config import settings
from app.models.schemas import ExecutionResult

logger = logging.getLogger(__name__)


async def execute_script(
    script: str,
    language: str,
    timeout: int = 30,
) -> ExecutionResult:
    """
    Execute a script in a sandboxed subprocess.
    Writes the script to a temp file, runs it, captures output, and cleans up.

    NEVER executes raw user text — only scripts produced by the generation pipeline.
    """
    language = language.lower().replace("-", "_")
    timeout = min(timeout, settings.EXECUTION_TIMEOUT)

    if language == "html_css" or language == "html":
        return ExecutionResult(
            success=True,
            stdout=script,
            stderr="",
            exit_code=0,
            duration_ms=0,
        )

    if language == "sql":
        return await _execute_sql(script, timeout)

    # Map language to file extension and command
    lang_config = _get_lang_config(language)
    if lang_config is None:
        return ExecutionResult(
            success=False,
            stderr=f"Unsupported language for execution: {language}",
            exit_code=-1,
        )

    ext, cmd_parts = lang_config
    tmp_path: Path | None = None

    try:
        # Write script to temp file
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=ext,
            delete=False,
            encoding="utf-8",
            dir=str(settings.OUTPUT_DIR),
        )
        tmp.write(script)
        tmp.close()
        tmp_path = Path(tmp.name)

        cmd = cmd_parts + [str(tmp_path)]

        start = time.perf_counter()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(settings.OUTPUT_DIR),
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)

        stdout = _truncate(stdout_bytes.decode("utf-8", errors="replace"))
        stderr = _truncate(stderr_bytes.decode("utf-8", errors="replace"))

        return ExecutionResult(
            success=proc.returncode == 0,
            stdout=stdout,
            stderr=stderr,
            exit_code=proc.returncode or 0,
            duration_ms=duration_ms,
        )
    except asyncio.TimeoutError:
        return ExecutionResult(
            success=False,
            stderr=f"Execution timed out after {timeout} seconds.",
            exit_code=-1,
        )
    except FileNotFoundError as exc:
        return ExecutionResult(
            success=False,
            stderr=f"Runtime not found: {exc}",
            exit_code=-1,
        )
    except Exception as exc:
        logger.error("Execution error: %s", exc, exc_info=True)
        return ExecutionResult(
            success=False,
            stderr=str(exc),
            exit_code=-1,
        )
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


async def _execute_sql(script: str, timeout: int) -> ExecutionResult:
    """Execute SQL against an in-memory SQLite database."""
    start = time.perf_counter()
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        # Execute all statements
        cursor.executescript(script)
        # Try to fetch results from last SELECT
        lines: list[str] = []
        try:
            cursor.execute(script.strip().split(";")[-2] + ";")  # re-run last statement
            rows = cursor.fetchall()
            if rows:
                if cursor.description:
                    headers = [d[0] for d in cursor.description]
                    lines.append("\t".join(headers))
                for row in rows:
                    lines.append("\t".join(str(v) for v in row))
        except Exception:
            lines.append("SQL executed successfully (no result set).")
        conn.close()
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ExecutionResult(
            success=True,
            stdout="\n".join(lines),
            exit_code=0,
            duration_ms=duration_ms,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ExecutionResult(
            success=False,
            stderr=str(exc),
            exit_code=1,
            duration_ms=duration_ms,
        )


def _get_lang_config(language: str) -> tuple[str, list[str]] | None:
    """Return (file_extension, command_parts) for the language."""
    python_cmd = sys.executable or "python"
    configs: dict[str, tuple[str, list[str]]] = {
        "python": (".py", [python_cmd]),
        "javascript": (".js", ["node"]),
        "typescript": (".ts", ["node"]),
        "bash": (".sh", ["bash"]),
        "powershell": (".ps1", ["powershell", "-ExecutionPolicy", "Bypass", "-File"]),
    }
    return configs.get(language)


def _truncate(text: str) -> str:
    """Truncate output to max configured size."""
    if len(text) > settings.MAX_OUTPUT_SIZE:
        return text[: settings.MAX_OUTPUT_SIZE] + "\n... [output truncated]"
    return text
