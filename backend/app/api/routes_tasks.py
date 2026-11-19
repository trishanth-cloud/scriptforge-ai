"""
ScriptForge AI — Task Routes
CRUD operations for tasks and pipeline initiation.
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.database import get_db
from app.models.schemas import (
    ScriptUpdateRequest,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatus,
)
from app.modules.code_validation import validate_script
from app.modules.results_manager import (
    add_script_version,
    delete_task,
    get_task,
    list_tasks,
    save_execution_log,
    save_task,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """Create a new task from uploaded file IDs and trigger autonomous pipeline."""
    file_ids = payload.file_ids
    if not file_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file ID is required.",
        )

    # Verify all files exist
    with get_db() as db:
        for fid in file_ids:
            row = db.execute("SELECT id FROM files WHERE id = ?", (fid,)).fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File ID '{fid}' not found.",
                )

        task_id = uuid4().hex
        now_str = datetime.now(timezone.utc).isoformat()

        db.execute(
            """
            INSERT INTO tasks (id, status, created_at, updated_at, repair_attempts, version_history_json)
            VALUES (?, ?, ?, ?, 0, '[]')
            """,
            (task_id, TaskStatus.UPLOADED.value, now_str, now_str),
        )

        for fid in file_ids:
            db.execute(
                "INSERT INTO task_files (task_id, file_id) VALUES (?, ?)",
                (task_id, fid),
            )

    pipeline = request.app.state.pipeline
    # Schedule full pipeline run in background
    background_tasks.add_task(pipeline.run_full_pipeline, task_id)

    return pipeline._build_response(task_id)


@router.get("/", response_model=TaskListResponse)
def get_all_tasks(request: Request):
    """List all tasks ordered by creation time."""
    pipeline = request.app.state.pipeline
    raw_tasks = list_tasks()
    responses: list[TaskResponse] = []
    for t in raw_tasks:
        try:
            resp = pipeline._build_response(t["id"])
            responses.append(resp)
        except Exception as e:
            logger.warning("Error building response for task %s: %s", t["id"], e)
    return TaskListResponse(tasks=responses, total=len(responses))


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: str, request: Request):
    """Get full details of a specific task."""
    pipeline = request.app.state.pipeline
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    return pipeline._build_response(task_id)


@router.put("/{task_id}/script", response_model=TaskResponse)
async def update_task_script(
    task_id: str,
    payload: ScriptUpdateRequest,
    request: Request,
):
    """Update the generated script manually, revalidate, and save version."""
    pipeline = request.app.state.pipeline
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    language = payload.language.value if payload.language else (task.get("script_language") or "python")
    script = payload.script

    # Validate updated script
    validation = await validate_script(script, language)

    # Save to DB & record version
    save_task(
        task_id,
        generated_script=script,
        script_language=language,
        validation_json=validation.model_dump_json(),
        status=TaskStatus.AWAITING_APPROVAL.value,
    )
    add_script_version(task_id, script, language, reason="User manual edit")
    save_execution_log(
        task_id,
        "script_edited",
        details="Script manually updated by user",
    )

    return pipeline._build_response(task_id)


@router.post("/{task_id}/regenerate", response_model=TaskResponse)
async def regenerate_task_script(
    task_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """Re-run the pipeline to generate a fresh script."""
    pipeline = request.app.state.pipeline
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    # Reset status and run pipeline
    save_task(task_id, status=TaskStatus.ANALYZING.value, repair_attempts=0)
    background_tasks.add_task(pipeline.run_full_pipeline, task_id)

    return pipeline._build_response(task_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(task_id: str):
    """Delete a task and its associated execution logs."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    delete_task(task_id)
    return None
