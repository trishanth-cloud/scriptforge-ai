"""
ScriptForge AI — Pipeline Orchestrator
Full end-to-end pipeline: ingest → analyse → plan → generate → validate → execute.
"""

import json
import logging
from datetime import datetime, timezone

from app.models.schemas import (
    AnalysisResult,
    ExecutionPlan,
    TaskResponse,
    TaskStatus,
    FileResponse,
    ValidationResult,
    ExecutionResult,
    DebugReport,
    ScriptVersion,
)
from app.modules.file_ingestion import ingest_file, get_file_preview
from app.modules.text_analysis import analyze_content
from app.modules.task_classification import classify_task
from app.modules.planning import generate_plan
from app.modules.script_generation import generate_script
from app.modules.code_validation import validate_script
from app.modules.sandbox_execution import execute_script
from app.modules.error_correction import attempt_fix
from app.modules.results_manager import (
    save_task,
    get_task,
    add_script_version,
    save_execution_log,
)
from app.config import settings
from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the full ScriptForge AI processing pipeline."""

    def __init__(self, ai_engine: AIEngine) -> None:
        self.ai_engine = ai_engine

    # ── Full pipeline: ingest → validate ────────────────────────

    async def run_full_pipeline(self, task_id: str) -> TaskResponse:
        """Run the entire pipeline up to awaiting_approval."""
        try:
            task = get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # 1. Analysing — ingest files and analyse content
            save_task(task_id, status=TaskStatus.ANALYZING.value)
            save_execution_log(task_id, "pipeline_start", details="Starting full pipeline")

            combined_content = ""
            file_type = "text"
            for f in task["files"]:
                result = await ingest_file(f["file_path"], f["original_name"])
                combined_content += result["content"] + "\n"
                file_type = result["file_type"]

            analysis = await analyze_content(combined_content, file_type, self.ai_engine)
            save_task(task_id, analysis_json=analysis.model_dump_json())
            save_execution_log(task_id, "analysis_complete", details=analysis.summary)

            # 2. Planning — classify and plan
            save_task(task_id, status=TaskStatus.PLANNING.value)

            task_type, language, confidence = await classify_task(
                analysis, combined_content, self.ai_engine
            )
            save_task(task_id, task_type=task_type, recommended_language=language)

            plan = await generate_plan(analysis, task_type, language, self.ai_engine)
            save_task(task_id, execution_plan_json=plan.model_dump_json())
            save_execution_log(task_id, "plan_complete", details=plan.description)

            # 3. Generating — generate script
            save_task(task_id, status=TaskStatus.GENERATING.value)

            script_code, lang = await generate_script(
                combined_content, analysis, plan, language, self.ai_engine
            )
            save_task(task_id, generated_script=script_code, script_language=lang)
            add_script_version(task_id, script_code, lang, "Initial generation")
            save_execution_log(task_id, "generation_complete", details=f"Generated {lang} script")

            # 4. Validating
            save_task(task_id, status=TaskStatus.VALIDATING.value)

            validation = await validate_script(script_code, lang)
            save_task(task_id, validation_json=validation.model_dump_json())
            save_execution_log(
                task_id,
                "validation_complete",
                details=f"Valid: {validation.is_valid}, Errors: {len(validation.errors)}",
            )

            # 5. Awaiting approval
            save_task(task_id, status=TaskStatus.AWAITING_APPROVAL.value)
            save_execution_log(task_id, "awaiting_approval", details="Pipeline complete, awaiting user approval")

            return self._build_response(task_id)

        except Exception as exc:
            logger.error("Pipeline failed for task %s: %s", task_id, exc, exc_info=True)
            save_task(task_id, status=TaskStatus.ERROR.value, error_log=str(exc))
            save_execution_log(task_id, "pipeline_error", details=str(exc))
            return self._build_response(task_id)

    # ── Execution pipeline ──────────────────────────────────────

    async def execute_task(self, task_id: str) -> TaskResponse:
        """Execute the generated script with self-correction loop."""
        try:
            task = get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            if task["status"] != TaskStatus.AWAITING_APPROVAL.value:
                raise ValueError(
                    f"Task must be in awaiting_approval status, got {task['status']}"
                )

            script = task["generated_script"]
            language = task["script_language"]
            repair_attempts = task.get("repair_attempts", 0)

            # Execute
            save_task(task_id, status=TaskStatus.EXECUTING.value)
            save_execution_log(task_id, "execution_start", details="Executing script")

            result = await execute_script(script, language, settings.EXECUTION_TIMEOUT)
            save_execution_log(
                task_id,
                "execution_result",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
                duration_ms=result.duration_ms,
            )

            # Self-correction loop
            while not result.success and repair_attempts < settings.MAX_REPAIR_ATTEMPTS:
                repair_attempts += 1
                save_task(
                    task_id,
                    status=TaskStatus.DEBUGGING.value,
                    repair_attempts=repair_attempts,
                )
                save_execution_log(
                    task_id,
                    "debug_attempt",
                    details=f"Attempt {repair_attempts}",
                )

                debug_report = await attempt_fix(
                    script, language, result.stderr or str(result.exit_code), repair_attempts, self.ai_engine
                )
                if debug_report.revised_script and debug_report.revised_script != script:
                    script = debug_report.revised_script
                    save_task(task_id, generated_script=script)
                    add_script_version(
                        task_id, script, language, f"Auto-fix attempt {repair_attempts}"
                    )

                    # Re-validate
                    validation = await validate_script(script, language)
                    save_task(task_id, validation_json=validation.model_dump_json())

                    # Re-execute
                    save_task(task_id, status=TaskStatus.EXECUTING.value)
                    result = await execute_script(
                        script, language, settings.EXECUTION_TIMEOUT
                    )
                    save_execution_log(
                        task_id,
                        "re_execution_result",
                        stdout=result.stdout,
                        stderr=result.stderr,
                        exit_code=result.exit_code,
                        duration_ms=result.duration_ms,
                    )
                else:
                    break  # AI couldn't produce a different script

            # Final status
            final_status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            save_task(
                task_id,
                status=final_status.value,
                execution_result_json=result.model_dump_json(),
                repair_attempts=repair_attempts,
            )
            save_execution_log(task_id, "pipeline_complete", details=f"Status: {final_status.value}")

            return self._build_response(task_id)

        except Exception as exc:
            logger.error("Execution failed for task %s: %s", task_id, exc, exc_info=True)
            save_task(task_id, status=TaskStatus.FAILED.value, error_log=str(exc))
            save_execution_log(task_id, "execution_error", details=str(exc))
            return self._build_response(task_id)

    # ── Helpers ─────────────────────────────────────────────────

    def _build_response(self, task_id: str) -> TaskResponse:
        """Build a TaskResponse from the current DB state."""
        task = get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        files = [
            FileResponse(
                id=f["id"],
                filename=f["filename"],
                original_name=f["original_name"],
                content_type=f.get("content_type"),
                file_size=f["file_size"],
                upload_time=f["upload_time"],
                preview=f.get("content_preview"),
            )
            for f in task.get("files", [])
        ]

        analysis = None
        if task.get("analysis_json"):
            analysis = AnalysisResult.model_validate_json(task["analysis_json"])

        plan = None
        if task.get("execution_plan_json"):
            plan = ExecutionPlan.model_validate_json(task["execution_plan_json"])

        validation = None
        if task.get("validation_json"):
            validation = ValidationResult.model_validate_json(task["validation_json"])

        execution_result = None
        if task.get("execution_result_json"):
            execution_result = ExecutionResult.model_validate_json(task["execution_result_json"])

        versions = []
        if task.get("version_history_json"):
            raw = json.loads(task["version_history_json"])
            versions = [ScriptVersion(**v) for v in raw]

        return TaskResponse(
            id=task["id"],
            status=TaskStatus(task["status"]),
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            files=files,
            task_type=task.get("task_type"),
            recommended_language=task.get("recommended_language"),
            analysis=analysis,
            execution_plan=plan,
            generated_script=task.get("generated_script"),
            script_language=task.get("script_language"),
            validation_result=validation,
            execution_result=execution_result,
            repair_attempts=task.get("repair_attempts", 0),
            versions=versions,
        )
