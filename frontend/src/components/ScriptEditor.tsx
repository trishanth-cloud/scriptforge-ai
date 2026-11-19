"use client";

import { useState, useCallback } from "react";
import Editor from "@monaco-editor/react";
import {
  Copy,
  Download,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Save,
  Loader2,
  AlertTriangle,
  Shield,
} from "lucide-react";
import { toast } from "sonner";
import * as api from "@/lib/api";
import { TaskResponse, ValidationResult } from "@/lib/types";

interface ScriptEditorProps {
  task: TaskResponse;
  onTaskUpdate: (task: TaskResponse) => void;
}

const LANG_MAP: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  bash: "shell",
  powershell: "powershell",
  sql: "sql",
  html_css: "html",
};

const LANG_COLORS: Record<string, string> = {
  python: "bg-accent-blue/15 text-accent-blue",
  javascript: "bg-accent-yellow/15 text-accent-yellow",
  typescript: "bg-accent-blue/15 text-accent-blue",
  bash: "bg-accent-green/15 text-accent-green",
  powershell: "bg-accent-blue/15 text-accent-blue",
  sql: "bg-accent-cyan/15 text-accent-cyan",
  html_css: "bg-accent-red/15 text-accent-red",
};

export default function ScriptEditor({ task, onTaskUpdate }: ScriptEditorProps) {
  const [editedScript, setEditedScript] = useState(task.generated_script || "");
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [localValidation, setLocalValidation] = useState<ValidationResult | null>(
    task.validation_result || null
  );

  const lang = task.script_language || "python";
  const monacoLang = LANG_MAP[lang] || "plaintext";

  const handleChange = useCallback(
    (value: string | undefined) => {
      const v = value || "";
      setEditedScript(v);
      setHasChanges(v !== task.generated_script);
    },
    [task.generated_script]
  );

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(editedScript);
    toast.success("Copied to clipboard");
  }, [editedScript]);

  const handleDownload = useCallback(async () => {
    try {
      const blob = await api.downloadScript(task.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `script.${lang === "html_css" ? "html" : lang === "javascript" ? "js" : lang === "typescript" ? "ts" : lang === "powershell" ? "ps1" : lang === "bash" ? "sh" : lang}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Script downloaded");
    } catch {
      toast.error("Download failed");
    }
  }, [task.id, lang]);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      const updated = await api.updateScript(task.id, editedScript, lang);
      onTaskUpdate(updated);
      setHasChanges(false);
      toast.success("Script saved");
    } catch {
      toast.error("Failed to save script");
    } finally {
      setIsSaving(false);
    }
  }, [task.id, editedScript, lang, onTaskUpdate]);

  const handleRegenerate = useCallback(async () => {
    setIsRegenerating(true);
    try {
      const updated = await api.regenerateScript(task.id);
      onTaskUpdate(updated);
      setEditedScript(updated.generated_script || "");
      setHasChanges(false);
      setLocalValidation(null);
      toast.success("Script regenerated");
    } catch {
      toast.error("Regeneration failed");
    } finally {
      setIsRegenerating(false);
    }
  }, [task.id, onTaskUpdate]);

  const handleValidate = useCallback(async () => {
    setIsValidating(true);
    try {
      const result = await api.validateScript(task.id);
      setLocalValidation(result);
      if (result.is_valid) {
        toast.success("Script is valid!");
      } else {
        toast.error(`Found ${result.errors.length} error(s)`);
      }
    } catch {
      toast.error("Validation failed");
    } finally {
      setIsValidating(false);
    }
  }, [task.id]);

  if (!task.generated_script) return null;

  return (
    <div className="bg-surface rounded-xl border border-surface-border overflow-hidden animate-fade-in">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
              LANG_COLORS[lang] || "bg-surface-lighter text-foreground/70"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-current" />
            {lang.replace("_", "/")}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {hasChanges && (
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-primary text-white hover:bg-primary-hover disabled:opacity-50 transition-colors"
            >
              {isSaving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              Save
            </button>
          )}
          <button
            onClick={handleCopy}
            className="p-1.5 text-foreground/40 hover:text-foreground/70 transition-colors"
            title="Copy"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 text-foreground/40 hover:text-foreground/70 transition-colors"
            title="Download"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={handleRegenerate}
            disabled={isRegenerating}
            className="p-1.5 text-foreground/40 hover:text-foreground/70 disabled:opacity-50 transition-colors"
            title="Regenerate"
          >
            {isRegenerating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={handleValidate}
            disabled={isValidating}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-surface-lighter text-foreground/70 hover:text-foreground/90 disabled:opacity-50 transition-colors"
          >
            {isValidating ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Shield className="w-3.5 h-3.5" />
            )}
            Validate
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="h-[400px]">
        <Editor
          language={monacoLang}
          theme="vs-dark"
          value={editedScript}
          onChange={handleChange}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: "on",
            wordWrap: "on",
            fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
            padding: { top: 12 },
            scrollBeyondLastLine: false,
            renderLineHighlight: "gutter",
            smoothScrolling: true,
          }}
        />
      </div>

      {/* Validation Results */}
      {localValidation && (
        <div className="border-t border-surface-border px-4 py-3">
          {localValidation.is_valid ? (
            <div className="flex items-center gap-2 text-sm text-accent-green">
              <CheckCircle2 className="w-4 h-4" />
              <span>Script is valid</span>
            </div>
          ) : (
            <div className="space-y-2">
              {localValidation.errors.map((err, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 text-sm text-accent-red"
                >
                  <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span className="font-mono text-xs">{err}</span>
                </div>
              ))}
              {localValidation.warnings.map((w, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 text-sm text-accent-yellow"
                >
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span className="font-mono text-xs">{w}</span>
                </div>
              ))}
              {localValidation.suggestions.map((s, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 text-sm text-accent-blue"
                >
                  <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  <span className="font-mono text-xs">{s}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
