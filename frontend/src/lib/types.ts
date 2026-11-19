export enum TaskStatus {
  UPLOADED = "uploaded",
  ANALYZING = "analyzing",
  PLANNING = "planning",
  GENERATING = "generating",
  VALIDATING = "validating",
  READY = "ready",
  AWAITING_APPROVAL = "awaiting_approval",
  EXECUTING = "executing",
  DEBUGGING = "debugging",
  COMPLETED = "completed",
  FAILED = "failed",
  ERROR = "error",
}

export enum ScriptLanguage {
  PYTHON = "python",
  JAVASCRIPT = "javascript",
  TYPESCRIPT = "typescript",
  BASH = "bash",
  POWERSHELL = "powershell",
  SQL = "sql",
  HTML_CSS = "html_css",
}

export interface FileResponse {
  id: string;
  filename: string;
  original_name: string;
  content_type?: string;
  file_size: number;
  upload_time: string;
  preview?: string;
}

export interface AnalysisResult {
  summary: string;
  extracted_instructions: string[];
  detected_variables: string[];
  dependencies: string[];
  ambiguities: string[];
  task_type: string;
  recommended_language: string;
  confidence: number;
  explanation: string;
}

export interface ExecutionPlanStep {
  step_number: number;
  description: string;
  details?: string;
}

export interface ExecutionPlan {
  steps: (string | ExecutionPlanStep)[];
  language: string;
  estimated_complexity: string;
  requires_approval: boolean;
  warnings: string[];
  description: string;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export interface ExecutionResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  output_files: string[];
}

export interface DebugReport {
  original_error: string;
  diagnosis: string;
  fix_applied: string;
  attempt_number: number;
  resolved: boolean;
  revised_script: string;
}

export interface ScriptVersion {
  version: number;
  script: string;
  language: string;
  timestamp: string;
  change_reason: string;
}

export interface TaskResponse {
  id: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  files: FileResponse[];
  task_type?: string;
  recommended_language?: string;
  analysis?: AnalysisResult;
  execution_plan?: ExecutionPlan;
  generated_script?: string;
  script_language?: string;
  validation_result?: ValidationResult;
  execution_result?: ExecutionResult;
  debug_reports: DebugReport[];
  repair_attempts: number;
  versions: ScriptVersion[];
}

export interface TaskListResponse {
  tasks: TaskResponse[];
  total: number;
}

export const PROCESSING_STATUSES: TaskStatus[] = [
  TaskStatus.ANALYZING,
  TaskStatus.PLANNING,
  TaskStatus.GENERATING,
  TaskStatus.VALIDATING,
];

export const ACTIVE_STATUSES: TaskStatus[] = [
  ...PROCESSING_STATUSES,
  TaskStatus.EXECUTING,
  TaskStatus.DEBUGGING,
];

export function isProcessing(status: TaskStatus): boolean {
  return PROCESSING_STATUSES.includes(status);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}
