"""
ScriptForge AI — Results Routes
Endpoints for downloading generated scripts and retrieving version history and logs.
"""

import io
import json
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models.schemas import ScriptVersion
from app.modules.results_manager import get_task, get_versions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["Results"])

EXT_MAP = {
    "python": "py",
    "javascript": "js",
    "typescript": "ts",
    "bash": "sh",
    "powershell": "ps1",
    "sql": "sql",
    "html_css": "html",
    "html": "html",
}


@router.get("/{task_id}/download")
def download_script(task_id: str):
    """Download the generated script as a file with the proper extension."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    script = task.get("generated_script")
    if not script:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No script generated for this task.",
        )

    lang = (task.get("script_language") or "python").lower()
    ext = EXT_MAP.get(lang, "txt")
    filename = f"scriptforge_{task_id[:8]}.{ext}"

    stream = io.BytesIO(script.encode("utf-8"))
    return StreamingResponse(
        stream,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{task_id}/versions", response_model=list[ScriptVersion])
def get_task_versions(task_id: str):
    """Get the version history of the generated script for this task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    raw_versions = get_versions(task_id)
    return [ScriptVersion(**v) for v in raw_versions]


@router.get("/{task_id}/logs")
def get_task_logs(task_id: str):
    """Get execution logs for this task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )

    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM execution_logs WHERE task_id = ? ORDER BY timestamp ASC",
            (task_id,),
        ).fetchall()
        return [dict(r) for r in rows]
