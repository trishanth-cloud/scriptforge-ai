"""
ScriptForge AI — Integration Test for Pipeline
"""

import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

from app.config import settings
from app.database import get_db, init_db
from app.models.schemas import TaskStatus
from app.services.ai_engine import AIEngine
from app.services.pipeline import Pipeline


def test_full_pipeline_flow():
    init_db()
    ai_engine = AIEngine()
    pipeline = Pipeline(ai_engine)

    # 1. Create a test instruction file
    instruction_text = """
Task: Read the server log file and count the number of 404 and 500 status codes.
Input: Log lines in standard Apache format.
Output: Print total 404 count and 500 count to stdout.
"""
    test_path = settings.UPLOAD_DIR / "test_instructions.txt"
    test_path.write_text(instruction_text, encoding="utf-8")

    file_id = uuid4().hex
    now_str = datetime.now(timezone.utc).isoformat()

    try:
        with get_db() as db:
            db.execute(
                """
                INSERT INTO files (id, filename, original_name, content_type, file_size, file_path, encoding, upload_time, content_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    "instructions.txt",
                    "instructions.txt",
                    "text/plain",
                    len(instruction_text),
                    str(test_path),
                    "utf-8",
                    now_str,
                    instruction_text[:200],
                ),
            )

            task_id = uuid4().hex
            db.execute(
                """
                INSERT INTO tasks (id, status, created_at, updated_at, repair_attempts, version_history_json)
                VALUES (?, ?, ?, ?, 0, '[]')
                """,
                (task_id, TaskStatus.UPLOADED.value, now_str, now_str),
            )

            db.execute(
                "INSERT INTO task_files (task_id, file_id) VALUES (?, ?)",
                (task_id, file_id),
            )

        # 2. Run pipeline
        resp = asyncio.run(pipeline.run_full_pipeline(task_id))

        assert resp.status == TaskStatus.AWAITING_APPROVAL
        assert resp.generated_script is not None
        assert len(resp.generated_script) > 0
        assert resp.validation_result is not None
        assert resp.validation_result.is_valid is True

        # 3. Execute approved task
        exec_resp = asyncio.run(pipeline.execute_task(task_id))
        assert exec_resp.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        assert exec_resp.execution_result is not None

    finally:
        if test_path.exists():
            test_path.unlink()
