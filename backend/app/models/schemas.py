"""
ScriptForge AI — Pydantic Schemas
All request/response models, enums, and data transfer objects.
These are the shared contract between backend modules, API routes, and frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────── Enums ────────────────────────────


class TaskStatus(str, Enum):
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    GENERATING = "generating"
    VALIDATING = "validating"
    READY = "ready"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    DEBUGGING = "debugging"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class ScriptLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    POWERSHELL = "powershell"
    SQL = "sql"
    HTML_CSS = "html_css"


class TaskType(str, Enum):
    DATA_TRANSFORMATION = "data_transformation"
    AUTOMATION = "automation"
    WEB_SCRAPING = "web_scraping"
    FILE_PROCESSING = "file_processing"
    API_INTEGRATION = "api_integration"
    DATABASE_OPERATION = "database_operation"
    SYSTEM_ADMINISTRATION = "system_administration"
    DATA_ANALYSIS = "data_analysis"
    WEB_APPLICATION = "web_application"
    UTILITY_SCRIPT = "utility_script"
    OTHER = "other"


# ──────────────────────── Request Models ───────────────────────


class TaskCreateRequest(BaseModel):
    """Request to create a task from uploaded file IDs."""
    file_ids: list[str] = Field(..., min_length=1, description="IDs of uploaded files")


class ScriptUpdateRequest(BaseModel):
    """Request to update a task's generated script."""
    script: str = Field(..., min_length=1)
    language: Optional[ScriptLanguage] = None


class ExecuteRequest(BaseModel):
    """Request to execute a generated script. Requires explicit approval."""
    approved: bool = Field(False, description="User must set to true to approve execution")


# ──────────────────────── Data Models ──────────────────────────


class FileResponse(BaseModel):
    """Uploaded file metadata."""
    id: str
    filename: str
    original_name: str
    content_type: Optional[str] = None
    file_size: int
    upload_time: str
    preview: Optional[str] = None


class AnalysisResult(BaseModel):
    """AI content analysis output."""
    summary: str = ""
    extracted_instructions: list[str] = Field(default_factory=list)
    detected_variables: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    task_type: str = ""
    recommended_language: str = ""
    confidence: float = 0.0
    explanation: str = ""


class ExecutionPlan(BaseModel):
    """Generated execution plan."""
    steps: list[str] = Field(default_factory=list)
    language: str = ""
    estimated_complexity: str = "medium"
    requires_approval: bool = True
    warnings: list[str] = Field(default_factory=list)
    description: str = ""


class ValidationResult(BaseModel):
    """Script validation result."""
    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    """Script execution result."""
    success: bool = False
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: int = 0
    output_files: list[str] = Field(default_factory=list)


class DebugReport(BaseModel):
    """Self-correction debug report."""
    original_error: str = ""
    diagnosis: str = ""
    fix_applied: str = ""
    attempt_number: int = 0
    resolved: bool = False
    revised_script: str = ""


class ScriptVersion(BaseModel):
    """A single version entry in the script history."""
    version: int
    script: str
    language: str
    timestamp: str
    change_reason: str = ""


# ──────────────────────── Response Models ──────────────────────


class TaskResponse(BaseModel):
    """Full task details returned by the API."""
    id: str
    status: TaskStatus
    created_at: str
    updated_at: str
    files: list[FileResponse] = Field(default_factory=list)
    task_type: Optional[str] = None
    recommended_language: Optional[str] = None
    analysis: Optional[AnalysisResult] = None
    execution_plan: Optional[ExecutionPlan] = None
    generated_script: Optional[str] = None
    script_language: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    execution_result: Optional[ExecutionResult] = None
    debug_reports: list[DebugReport] = Field(default_factory=list)
    repair_attempts: int = 0
    versions: list[ScriptVersion] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    """Paginated task list."""
    tasks: list[TaskResponse]
    total: int


class PipelineStatusResponse(BaseModel):
    """Status response returned during pipeline processing."""
    task_id: str
    status: TaskStatus
    message: str = ""
    progress: Optional[float] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    app: str = "ScriptForge AI"
    version: str = "1.0.0"
