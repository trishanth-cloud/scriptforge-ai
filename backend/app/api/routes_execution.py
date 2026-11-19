"""
ScriptForge AI — Execution Routes
Endpoints for controlled script execution and validation.
"""

import logging
from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import ExecuteRequest, TaskResponse, TaskStatus
from app.modules.code_validation import validate_script
from app.modules.results_manager import get_task, save_execution_log, save_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["Execution"])


@router.post("/{task_id}/execute", response_model=TaskResponse)
async def execute_task_script(
    task_id: str,
    payload: ExecuteRequest,
    request: Request,
):
    """Execute the generated script in an isolated sandbox. Explicit user approval is mandatory."""
    if not payload.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution requires explicit user approval. Set 'approved: true'.",
        )

    pipeline = request.app.state.pipeline
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    if not task.get("generated_script"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No script generated for this task yet.",
        )

    # Ensure status allows execution
    allowed_statuses = [
        TaskStatus.AWAITING_APPROVAL.value,
        TaskStatus.COMPLETED.value,
        TaskStatus.FAILED.value,
    ]
    if task["status"] not in allowed_statuses:
        # Allow retry if already completed or failed, otherwise check awaiting_approval
        save_task(task_id, status=TaskStatus.AWAITING_APPROVAL.value)

    # Run the execution pipeline (includes self-correction if runtime error)
    response = await pipeline.execute_task(task_id)
    return response


@router.post("/{task_id}/validate", response_model=TaskResponse)
async def validate_task_script(
    task_id: str,
    request: Request,
):
    """Run syntax validation on the current script without executing it."""
    pipeline = request.app.state.pipeline
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    script = task.get("generated_script") or ""
    language = task.get("script_language") or "python"

    validation = await validate_script(script, language)
    save_task(task_id, validation_json=validation.model_dump_json())
    save_execution_log(
        task_id,
        "validation_check",
        details=f"Valid: {validation.is_valid}, Errors: {len(validation.errors)}",
    )

    return pipeline._build_response(task_id)
