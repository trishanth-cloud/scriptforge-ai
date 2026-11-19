"""
ScriptForge AI — Text Analysis Module
AI-powered content understanding.
"""

import logging

from app.models.schemas import AnalysisResult

logger = logging.getLogger(__name__)


async def analyze_content(content: str, file_type: str, ai_engine) -> AnalysisResult:
    """
    Use the AI engine to analyze text content.
    Returns an AnalysisResult with extracted instructions, variables,
    dependencies, ambiguities, task type, and recommended language.
    """
    try:
        result_dict = await ai_engine.analyze(content, file_type)
        return AnalysisResult(
            summary=result_dict.get("summary", ""),
            extracted_instructions=result_dict.get("extracted_instructions", []),
            detected_variables=result_dict.get("detected_variables", []),
            dependencies=result_dict.get("dependencies", []),
            ambiguities=result_dict.get("ambiguities", []),
            task_type=result_dict.get("task_type", "other"),
            recommended_language=result_dict.get("recommended_language", "python"),
            confidence=float(result_dict.get("confidence", 0.5)),
            explanation=result_dict.get("explanation", ""),
        )
    except Exception as exc:
        logger.error("Content analysis failed: %s", exc, exc_info=True)
        return AnalysisResult(
            summary="Analysis failed — using defaults.",
            task_type="other",
            recommended_language="python",
            confidence=0.0,
            explanation=str(exc),
        )
