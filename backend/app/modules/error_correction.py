"""
ScriptForge AI — Error Correction Module
AI-powered self-correction for failed scripts.
"""

import logging

from app.models.schemas import DebugReport

logger = logging.getLogger(__name__)


async def attempt_fix(
    script: str,
    language: str,
    error: str,
    attempt: int,
    ai_engine,
) -> DebugReport:
    """
    Send the script and error to the AI engine for diagnosis and correction.
    Max attempts is enforced by the caller (Pipeline).
    """
    logger.info("Attempting fix #%d for %s script", attempt, language)
    try:
        result = await ai_engine.debug(script, error, language)
        revised = result.get("revised_script", script)
        # Strip code fences if present
        lines = revised.strip().splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        revised = "\n".join(lines)

        return DebugReport(
            original_error=error,
            diagnosis=result.get("diagnosis", ""),
            fix_applied=result.get("fix_applied", ""),
            attempt_number=attempt,
            resolved=result.get("resolved", False),
            revised_script=revised,
        )
    except Exception as exc:
        logger.error("Error correction attempt %d failed: %s", attempt, exc, exc_info=True)
        return DebugReport(
            original_error=error,
            diagnosis=f"Auto-fix failed: {exc}",
            fix_applied="",
            attempt_number=attempt,
            resolved=False,
            revised_script=script,
        )
