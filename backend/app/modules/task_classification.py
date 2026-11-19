"""
ScriptForge AI — Task Classification Module
Determine task type and recommended language.
"""

import logging

from app.models.schemas import AnalysisResult

logger = logging.getLogger(__name__)


async def classify_task(
    analysis: AnalysisResult, content: str, ai_engine
) -> tuple[str, str, float]:
    """
    Classify the task based on analysis results.
    If the analysis confidence is below 0.7, use the AI engine for a second pass.
    Returns (task_type, recommended_language, confidence).
    """
    if analysis.confidence >= 0.7:
        logger.info("Using high-confidence analysis result directly (%.2f)", analysis.confidence)
        return analysis.task_type, analysis.recommended_language, analysis.confidence

    # Low confidence — ask AI for a focused classification
    logger.info("Low confidence (%.2f), requesting AI classification", analysis.confidence)
    try:
        result = await ai_engine.analyze(content, "text")
        task_type = result.get("task_type", analysis.task_type or "other")
        language = result.get("recommended_language", analysis.recommended_language or "python")
        confidence = float(result.get("confidence", 0.5))
        return task_type, language, confidence
    except Exception as exc:
        logger.warning("AI classification failed, using analysis defaults: %s", exc)
        return (
            analysis.task_type or "other",
            analysis.recommended_language or "python",
            analysis.confidence,
        )
