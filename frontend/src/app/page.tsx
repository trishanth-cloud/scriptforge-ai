"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import FileUpload from "@/components/FileUpload";
import FilePreview from "@/components/FilePreview";
import AnalysisPanel from "@/components/AnalysisPanel";
import ScriptEditor from "@/components/ScriptEditor";
import ExecutionConsole from "@/components/ExecutionConsole";
import ResultsPanel from "@/components/ResultsPanel";
import { useFileUpload } from "@/hooks/useFileUpload";
import { useTask } from "@/hooks/useTask";
import { useExecution } from "@/hooks/useExecution";
import { useTaskStore } from "@/store/taskStore";
import { TaskStatus, isProcessing } from "@/lib/types";
import { Sparkles, Terminal, FileCode, Plus, History, Loader2, ArrowRight } from "lucide-react";
import * as api from "@/lib/api";

export default function DashboardPage() {
  const store = useTaskStore();
  const { files, isUploading, uploadFiles, removeFile, clearFiles } = useFileUpload();
  const { task, createTask, refreshTask, startPolling } = useTask();
  const { isExecuting, executeScript } = useExecution();
  const [showHistory, setShowHistory] = useState(false);

  // Load existing tasks on mount
  useEffect(() => {
    async function loadTasks() {
      try {
        const resp = await api.listTasks();
        if (resp && resp.tasks) {
          resp.tasks.forEach((t) => store.addTask(t));
          if (!store.currentTask && resp.tasks.length > 0) {
            store.setCurrentTask(resp.tasks[0]);
          }
        }
      } catch {
        // backend might still be starting
      }
    }
    loadTasks();
  }, []);

  const currentTask = store.currentTask;

  // Handle file upload and immediate task trigger
  const handleUpload = async (newFiles: File[]) => {
    const uploaded = await uploadFiles(newFiles);
    if (uploaded && uploaded.length > 0) {
      const fileIds = uploaded.map((f) => f.id);
      const created = await createTask(fileIds);
      if (created) {
        store.setCurrentTask(created);
      }
    }
  };

  const handleTaskUpdate = (updatedTask: typeof currentTask) => {
    if (updatedTask) {
      store.setCurrentTask(updatedTask);
      store.updateTask(updatedTask);
    }
  };

  const handleNewTask = () => {
    clearFiles();
    store.setCurrentTask(null);
  };

  const currentFiles = currentTask?.files?.length
    ? currentTask.files
    : files;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />

      {/* Action Bar */}
      <div className="bg-surface/60 border-b border-surface-border px-6 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-400">Current Task:</span>
          {currentTask ? (
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono bg-surface-light px-2 py-0.5 rounded text-primary-light border border-surface-border">
                {currentTask.id.substring(0, 8)}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full capitalize font-medium border border-primary/30 bg-primary/10 text-primary-light">
                {currentTask.status.replace("_", " ")}
              </span>
              {currentTask.recommended_language && (
                <span className="text-xs font-mono bg-surface-lighter px-2 py-0.5 rounded text-slate-300">
                  {currentTask.recommended_language}
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-slate-500 italic">No active task. Upload a file to begin.</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {currentTask && (
            <button
              onClick={handleNewTask}
              className="flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md bg-surface-light hover:bg-surface-lighter text-slate-200 border border-surface-border transition-colors"
            >
              <Plus className="w-3.5 h-3.5 text-primary-light" />
              New Task
            </button>
          )}

          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md bg-surface-light hover:bg-surface-lighter text-slate-200 border border-surface-border transition-colors"
          >
            <History className="w-3.5 h-3.5 text-slate-400" />
            History ({store.tasks.length})
          </button>
        </div>
      </div>

      {/* History Drawer Modal */}
      {showHistory && (
        <div className="bg-surface border-b border-surface-border px-6 py-4 animate-slide-up">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <History className="w-4 h-4 text-primary-light" />
              Previous Tasks
            </h3>
            <button
              onClick={() => setShowHistory(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Close
            </button>
          </div>
          {store.tasks.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No previous tasks recorded yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-h-48 overflow-y-auto pr-1">
              {store.tasks.map((t) => (
                <div
                  key={t.id}
                  onClick={() => {
                    store.setCurrentTask(t);
                    setShowHistory(false);
                  }}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                    currentTask?.id === t.id
                      ? "border-primary bg-primary/10"
                      : "border-surface-border bg-surface-light hover:border-slate-500"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-mono text-slate-300 font-medium">
                      {t.id.substring(0, 8)}
                    </span>
                    <span className="capitalize text-[11px] text-slate-400">
                      {t.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">
                    {t.files?.[0]?.original_name || "Untitled task"}
                  </p>
                  <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                    <span>{t.recommended_language || "python"}</span>
                    <span>{new Date(t.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 max-w-[1800px] w-full mx-auto">
        {/* Left Column (Ingestion & AI Analysis) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* File Upload Component */}
          <div className="bg-surface rounded-xl border border-surface-border p-5 shadow-lg">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-primary-light" />
              1. File Ingestion
            </h2>
            <FileUpload
              files={currentFiles}
              isUploading={isUploading}
              onUpload={handleUpload}
              onRemove={removeFile}
            />
          </div>

          {/* File Preview Component */}
          {currentFiles.length > 0 && (
            <div className="bg-surface rounded-xl border border-surface-border p-5 shadow-lg">
              <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                <FileCode className="w-4 h-4 text-accent-blue" />
                Raw File Content
              </h2>
              <FilePreview files={currentFiles} />
            </div>
          )}

          {/* AI Analysis Component */}
          <div className="bg-surface rounded-xl border border-surface-border p-5 shadow-lg">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary-light" />
              2. AI Content Understanding & Plan
            </h2>
            <AnalysisPanel
              analysis={currentTask?.analysis}
              executionPlan={currentTask?.execution_plan}
              status={currentTask?.status || TaskStatus.UPLOADED}
            />
          </div>
        </div>

        {/* Right Column (Script Editor, Console, Results) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {/* Pipeline Active Status Banner */}
          {currentTask && isProcessing(currentTask.status) && (
            <div className="bg-primary/10 border border-primary/30 rounded-xl p-4 flex items-center justify-between animate-pulse">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-primary-light animate-spin" />
                <div>
                  <h4 className="text-sm font-medium text-slate-200 capitalize">
                    Autonomous Pipeline Running: {currentTask.status.replace("_", " ")}
                  </h4>
                  <p className="text-xs text-slate-400">
                    Extracting intent, planning architecture, and generating validated code...
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Script Editor */}
          <div className="bg-surface rounded-xl border border-surface-border p-5 shadow-lg flex-1 min-h-[420px]">
            <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-accent-cyan" />
              3. Generated Code & Validation
            </h2>
            {currentTask && currentTask.generated_script ? (
              <ScriptEditor task={currentTask} onTaskUpdate={handleTaskUpdate} />
            ) : (
              <div className="h-72 border border-dashed border-surface-border rounded-lg flex flex-col items-center justify-center text-center p-6 text-slate-500">
                <FileCode className="w-10 h-10 mb-2 opacity-40 text-slate-400" />
                <p className="text-sm text-slate-300 font-medium">No script generated yet</p>
                <p className="text-xs text-slate-500 max-w-sm mt-1">
                  Upload a file with instructions or data on the left to trigger autonomous script generation.
                </p>
              </div>
            )}
          </div>

          {/* Execution Console */}
          {currentTask && (
            <div className="bg-surface rounded-xl border border-surface-border p-5 shadow-lg">
              <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-accent-green" />
                4. Controlled Sandboxed Execution
              </h2>
              <ExecutionConsole
                task={currentTask}
                isExecuting={isExecuting}
                onExecute={(id) => executeScript(id)}
              />
            </div>
          )}

          {/* Results & Debug Panel */}
          {currentTask &&
            (currentTask.status === TaskStatus.COMPLETED ||
              currentTask.status === TaskStatus.FAILED ||
              currentTask.execution_result) && (
              <div className="bg-surface rounded-xl border border-surface-border p-5 shadow-lg">
                <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-accent-yellow" />
                  5. Execution Results & Self-Correction
                </h2>
                <ResultsPanel task={currentTask} />
              </div>
            )}
        </div>
      </div>
    </div>
  );
}
