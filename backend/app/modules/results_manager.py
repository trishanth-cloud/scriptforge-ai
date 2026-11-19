"""
ScriptForge AI — Results Manager Module
Database persistence for tasks, versions, and execution logs.
"""

import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.database import get_db

logger = logging.getLogger(__name__)


def save_task(task_id: str, **fields) -> None:
    """Update task fields in the database."""
    if not fields:
        return
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [task_id]
    with get_db() as db:
        db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    logger.debug("Task %s updated: %s", task_id, list(fields.keys()))


def get_task(task_id: str) -> dict | None:
    """Get a task from the database with its associated file list."""
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return None
        task = dict(row)

        # Attach files
        file_rows = db.execute(
            """
            SELECT f.* FROM files f
            JOIN task_files tf ON f.id = tf.file_id
            WHERE tf.task_id = ?
            """,
            (task_id,),
        ).fetchall()
        task["files"] = [dict(f) for f in file_rows]
    return task


def list_tasks() -> list[dict]:
    """List all tasks ordered by creation time (newest first)."""
    with get_db() as db:
        rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        tasks = []
        for row in rows:
            task = dict(row)
            file_rows = db.execute(
                """
                SELECT f.* FROM files f
                JOIN task_files tf ON f.id = tf.file_id
                WHERE tf.task_id = ?
                """,
                (task["id"],),
            ).fetchall()
            task["files"] = [dict(f) for f in file_rows]
            tasks.append(task)
    return tasks


def delete_task(task_id: str) -> None:
    """Delete a task and its associated file records from the database."""
    with get_db() as db:
        db.execute("DELETE FROM task_files WHERE task_id = ?", (task_id,))
        db.execute("DELETE FROM execution_logs WHERE task_id = ?", (task_id,))
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    logger.info("Task %s deleted", task_id)


def add_script_version(
    task_id: str, script: str, language: str, reason: str = ""
) -> None:
    """Append a new version entry to the task's version_history_json."""
    with get_db() as db:
        row = db.execute(
            "SELECT version_history_json FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return
        history = json.loads(row["version_history_json"] or "[]")
        version_num = len(history) + 1
        history.append(
            {
                "version": version_num,
                "script": script,
                "language": language,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "change_reason": reason,
            }
        )
        db.execute(
            "UPDATE tasks SET version_history_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(history), datetime.now(timezone.utc).isoformat(), task_id),
        )
    logger.debug("Task %s: version %d added", task_id, version_num)


def get_versions(task_id: str) -> list[dict]:
    """Get the version history for a task."""
    with get_db() as db:
        row = db.execute(
            "SELECT version_history_json FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return []
        return json.loads(row["version_history_json"] or "[]")


def save_execution_log(task_id: str, event_type: str, **data) -> None:
    """Save an execution log entry."""
    log_id = uuid4().hex
    with get_db() as db:
        db.execute(
            """
            INSERT INTO execution_logs (id, task_id, timestamp, event_type, details, stdout, stderr, exit_code, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                task_id,
                datetime.now(timezone.utc).isoformat(),
                event_type,
                data.get("details"),
                data.get("stdout"),
                data.get("stderr"),
                data.get("exit_code"),
                data.get("duration_ms"),
            ),
        )
    logger.debug("Execution log %s saved for task %s", log_id, task_id)
