"""
ScriptForge AI — Planning Module
Generate step-by-step execution plans.
"""

import logging

from app.models.schemas import AnalysisResult, ExecutionPlan

logger = logging.getLogger(__name__)


async def generate_plan(
    analysis: AnalysisResult,
    task_type: str,
    language: str,
    ai_engine,
) -> ExecutionPlan:
    """
    Generate an execution plan from the analysis, task type, and language.
    """
    try:
        plan_dict = await ai_engine.plan(
            analysis.model_dump(),
            task_type,
            language,
        )
        return ExecutionPlan(
            steps=plan_dict.get("steps", []),
            language=plan_dict.get("language", language),
            estimated_complexity=plan_dict.get("estimated_complexity", "medium"),
            requires_approval=plan_dict.get("requires_approval", True),
            warnings=plan_dict.get("warnings", []),
            description=plan_dict.get("description", ""),
        )
    except Exception as exc:
        logger.error("Plan generation failed: %s", exc, exc_info=True)
        return ExecutionPlan(
            steps=["Read input", "Process data", "Write output"],
            language=language,
            estimated_complexity="medium",
            description=f"Default plan (generation failed: {exc})",
            warnings=["Plan was auto-generated due to an error."],
        )
