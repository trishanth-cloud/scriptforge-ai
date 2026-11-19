"use client";

import {
  CheckCircle2,
  XCircle,
  Download,
  Clock,
  Code,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import * as api from "@/lib/api";
import {
  TaskResponse,
  TaskStatus,
  formatDuration,
} from "@/lib/types";

interface ResultsPanelProps {
  task: TaskResponse;
}

export default function ResultsPanel({ task }: ResultsPanelProps) {
  const isCompleted = task.status === TaskStatus.COMPLETED;
  const isFailed =
    task.status === TaskStatus.FAILED || task.status === TaskStatus.ERROR;

  if (!isCompleted && !isFailed) return null;

  const exec = task.execution_result;

  const handleDownloadScript = async () => {
    try {
      const blob = await api.downloadScript(task.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ext =
        task.script_language === "javascript"
          ? "js"
          : task.script_language === "typescript"
          ? "ts"
          : task.script_language === "bash"
          ? "sh"
          : task.script_language === "powershell"
          ? "ps1"
          : task.script_language === "html_css"
          ? "html"
          : task.script_language || "txt";
      a.download = `script.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Script downloaded");
    } catch {
      toast.error("Download failed");
    }
  };

  const handleDownloadLog = () => {
    const content = [
      `--- ScriptForge AI Output Log ---`,
      `Task ID: ${task.id}`,
      `Status: ${task.status}`,
      `Language: ${task.script_language || "unknown"}`,
      exec ? `Duration: ${formatDuration(exec.duration_ms)}` : "",
      exec ? `Exit Code: ${exec.exit_code}` : "",
      "",
      "=== STDOUT ===",
      exec?.stdout || "(empty)",
      "",
      "=== STDERR ===",
      exec?.stderr || "(empty)",
    ].join("\n");
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "output.log";
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Log downloaded");
  };

  return (
    <div className="bg-surface rounded-xl border border-surface-border overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <h3 className="text-sm font-semibold text-foreground/90">Results</h3>
        {isCompleted ? (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent-green/15 text-accent-green">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Completed
          </span>
        ) : (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent-red/15 text-accent-red">
            <XCircle className="w-3.5 h-3.5" />
            Failed
          </span>
        )}
      </div>

      {/* Summary Card */}
      <div className="px-4 py-4 border-b border-surface-border/50">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-foreground/40 mb-1">Language</div>
            <div className="flex items-center justify-center gap-1.5">
              <Code className="w-3.5 h-3.5 text-primary" />
              <span className="text-sm font-medium text-foreground/80 capitalize">
                {(task.script_language || "unknown").replace("_", "/")}
              </span>
            </div>
          </div>
          <div>
            <div className="text-xs text-foreground/40 mb-1">Duration</div>
            <div className="flex items-center justify-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-primary" />
              <span className="text-sm font-medium text-foreground/80">
                {exec ? formatDuration(exec.duration_ms) : "—"}
              </span>
            </div>
          </div>
          <div>
            <div className="text-xs text-foreground/40 mb-1">Exit Code</div>
            <span
              className={`text-sm font-mono font-medium ${
                exec?.exit_code === 0
                  ? "text-accent-green"
                  : "text-accent-red"
              }`}
            >
              {exec?.exit_code ?? "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Script Preview */}
      {task.generated_script && (
        <div className="px-4 py-3 border-b border-surface-border/50">
          <div className="text-xs text-foreground/40 mb-2">Generated Script</div>
          <pre className="console-output text-foreground/60 max-h-32 overflow-auto bg-surface-light/30 rounded-lg p-3">
            {task.generated_script.length > 500
              ? task.generated_script.slice(0, 500) + "\n..."
              : task.generated_script}
          </pre>
        </div>
      )}

      {/* Output */}
      {exec?.stdout && (
        <div className="px-4 py-3 border-b border-surface-border/50">
          <div className="text-xs text-foreground/40 mb-2">Output</div>
          <pre className="console-output text-accent-green/80 max-h-48 overflow-auto bg-surface-light/30 rounded-lg p-3">
            {exec.stdout}
          </pre>
        </div>
      )}

      {/* Error details */}
      {isFailed && exec?.stderr && (
        <div className="px-4 py-3 border-b border-surface-border/50">
          <div className="text-xs text-foreground/40 mb-2">Error Details</div>
          <pre className="console-output text-accent-red/80 max-h-48 overflow-auto bg-surface-light/30 rounded-lg p-3">
            {exec.stderr}
          </pre>
        </div>
      )}

      {/* Debug Summary */}
      {isFailed && task.debug_reports.length > 0 && (
        <div className="px-4 py-3 border-b border-surface-border/50">
          <div className="text-xs text-foreground/40 mb-2">
            Debug Attempts ({task.debug_reports.length})
          </div>
          <div className="space-y-1.5">
            {task.debug_reports.map((r, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-xs bg-surface-light/30 rounded px-3 py-2"
              >
                <span className="text-foreground/60">
                  Attempt {r.attempt_number}: {r.diagnosis.slice(0, 60)}
                  {r.diagnosis.length > 60 ? "..." : ""}
                </span>
                {r.resolved ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-accent-green shrink-0" />
                ) : (
                  <XCircle className="w-3.5 h-3.5 text-accent-red shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Download Buttons */}
      <div className="px-4 py-3 flex gap-2">
        <button
          onClick={handleDownloadScript}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-primary text-white hover:bg-primary-hover transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Download Script
        </button>
        <button
          onClick={handleDownloadLog}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-surface-lighter text-foreground/70 hover:text-foreground/90 transition-colors"
        >
          <FileText className="w-3.5 h-3.5" />
          Download Log
        </button>
      </div>

      {/* Version History */}
      {task.versions && task.versions.length > 0 && (
        <div className="border-t border-surface-border px-4 py-3">
          <div className="text-xs text-foreground/40 mb-2">Version History</div>
          <div className="space-y-1.5">
            {task.versions.map((v) => (
              <div
                key={v.version}
                className="flex items-center justify-between text-xs bg-surface-light/30 rounded px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-primary">v{v.version}</span>
                  <span className="text-foreground/50">{v.change_reason}</span>
                </div>
                <span className="text-foreground/30">
                  {new Date(v.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
