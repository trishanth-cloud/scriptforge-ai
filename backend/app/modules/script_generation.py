"""
ScriptForge AI — Script Generation Module
Generate production-quality scripts from analysis and plans.
"""

import logging

from app.models.schemas import AnalysisResult, ExecutionPlan

logger = logging.getLogger(__name__)


async def generate_script(
    content: str,
    analysis: AnalysisResult,
    plan: ExecutionPlan,
    language: str,
    ai_engine,
) -> tuple[str, str]:
    """
    Generate a script using the AI engine.
    Returns (script_code, language).
    """
    try:
        script_code = await ai_engine.generate(
            content,
            analysis.model_dump(),
            plan.model_dump(),
            language,
        )
        # Clean up markdown fences if present
        script_code = _strip_code_fences(script_code)
        return script_code, language
    except Exception as exc:
        logger.error("Script generation failed: %s", exc, exc_info=True)
        # Return a minimal placeholder so the pipeline doesn't break
        fallback = _fallback_script(language, str(exc))
        return fallback, language


def _strip_code_fences(code: str) -> str:
    """Remove markdown code fences from AI output."""
    lines = code.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _fallback_script(language: str, error_msg: str) -> str:
    """Generate a minimal fallback script."""
    comment = "#" if language in ("python", "bash", "powershell") else "//"
    if language == "sql":
        comment = "--"
    return (
        f"{comment} ScriptForge AI — Script generation failed\n"
        f"{comment} Error: {error_msg}\n"
        f"{comment} Please try regenerating or editing manually.\n"
    )
