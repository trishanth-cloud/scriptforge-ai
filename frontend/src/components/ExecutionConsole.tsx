"use client";

import { useState, useCallback } from "react";
import {
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  Terminal,
  Clock,
  AlertTriangle,
  Bug,
} from "lucide-react";
import { TaskResponse, TaskStatus, formatDuration } from "@/lib/types";

interface ExecutionConsoleProps {
  task: TaskResponse;
  isExecuting: boolean;
  onExecute: (taskId: string) => void;
}

export default function ExecutionConsole({
  task,
  isExecuting,
  onExecute,
}: ExecutionConsoleProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleExecute = useCallback(() => {
    setShowConfirm(false);
    onExecute(task.id);
  }, [task.id, onExecute]);

  const exec = task.execution_result;
  const isRunning = isExecuting || task.status === TaskStatus.EXECUTING;
  const isComplete = !!exec;
  const isSuccess = exec?.success;

  return (
    <div className="bg-surface rounded-xl border border-surface-border overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-foreground/50" />
          <h3 className="text-sm font-semibold text-foreground/90">
            Execution Console
          </h3>
          {/* Status indicator */}
          {isRunning ? (
            <span className="flex items-center gap-1.5 text-xs text-primary">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Running
            </span>
          ) : isComplete ? (
            isSuccess ? (
              <span className="flex items-center gap-1.5 text-xs text-accent-green">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Success
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-xs text-accent-red">
                <XCircle className="w-3.5 h-3.5" />
                Failed
              </span>
            )
          ) : null}
        </div>

        {/* Run button */}
        {!isRunning && (
          <button
            onClick={() => setShowConfirm(true)}
            disabled={isExecuting}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-md bg-accent-green text-white hover:bg-accent-green/80 disabled:opacity-50 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            Run Script
          </button>
        )}
      </div>

      {/* Confirm Dialog */}
      {showConfirm && (
        <div className="px-4 py-3 bg-accent-yellow/10 border-b border-accent-yellow/20">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-accent-yellow shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground/90">
                Are you sure you want to execute this script?
              </p>
              <p className="text-xs text-foreground/50 mt-1">
                The script will run in a sandboxed environment with limited
                permissions.
              </p>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={handleExecute}
                  className="px-3 py-1.5 text-xs font-medium rounded-md bg-accent-green text-white hover:bg-accent-green/80 transition-colors"
                >
                  Yes, Execute
                </button>
                <button
                  onClick={() => setShowConfirm(false)}
                  className="px-3 py-1.5 text-xs font-medium rounded-md bg-surface-lighter text-foreground/70 hover:text-foreground/90 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Output */}
      {isRunning && !exec && (
        <div className="p-6 flex items-center justify-center">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
          <span className="ml-3 text-sm text-foreground/50">
            Executing script...
          </span>
        </div>
      )}

      {exec && (
        <div>
          {/* Metadata */}
          <div className="flex items-center gap-4 px-4 py-2.5 border-b border-surface-border/50 text-xs text-foreground/50">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              {formatDuration(exec.duration_ms)}
            </div>
            <div>
              Exit code:{" "}
              <span
                className={`font-mono ${
                  exec.exit_code === 0 ? "text-accent-green" : "text-accent-red"
                }`}
              >
                {exec.exit_code}
              </span>
            </div>
          </div>

          {/* stdout */}
          {exec.stdout && (
            <div className="border-b border-surface-border/50">
              <div className="px-4 py-1.5 text-[11px] text-foreground/40 uppercase tracking-wider">
                stdout
              </div>
              <div className="console-output px-4 pb-4 text-accent-green/80 max-h-64 overflow-auto">
                {exec.stdout}
              </div>
            </div>
          )}

          {/* stderr */}
          {exec.stderr && (
            <div className="border-b border-surface-border/50">
              <div className="px-4 py-1.5 text-[11px] text-foreground/40 uppercase tracking-wider">
                stderr
              </div>
              <div className="console-output px-4 pb-4 text-accent-red/80 max-h-48 overflow-auto">
                {exec.stderr}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Debug Reports */}
      {task.debug_reports && task.debug_reports.length > 0 && (
        <div className="border-t border-surface-border">
          <div className="px-4 py-2.5 flex items-center gap-2 text-xs text-foreground/50">
            <Bug className="w-3.5 h-3.5" />
            Debug Reports ({task.debug_reports.length} attempt
            {task.debug_reports.length > 1 ? "s" : ""})
          </div>
          <div className="px-4 pb-4 space-y-3">
            {task.debug_reports.map((report, i) => (
              <div
                key={i}
                className="bg-surface-light/30 rounded-lg p-3 text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-foreground/70">
                    Attempt {report.attempt_number}
                  </span>
                  {report.resolved ? (
                    <span className="text-accent-green flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Resolved
                    </span>
                  ) : (
                    <span className="text-accent-red flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> Unresolved
                    </span>
                  )}
                </div>
                <p className="text-foreground/50">
                  <strong className="text-foreground/60">Error:</strong>{" "}
                  {report.original_error}
                </p>
                <p className="text-foreground/50">
                  <strong className="text-foreground/60">Diagnosis:</strong>{" "}
                  {report.diagnosis}
                </p>
                <p className="text-foreground/50">
                  <strong className="text-foreground/60">Fix:</strong>{" "}
                  {report.fix_applied}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
