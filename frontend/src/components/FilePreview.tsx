"use client";

import { useState } from "react";
import { FileText } from "lucide-react";
import { FileResponse, formatFileSize } from "@/lib/types";

interface FilePreviewProps {
  files: FileResponse[];
}

export default function FilePreview({ files }: FilePreviewProps) {
  const [activeTab, setActiveTab] = useState(0);

  if (files.length === 0) return null;

  const active = files[activeTab] || files[0];

  return (
    <div className="bg-surface rounded-xl border border-surface-border overflow-hidden animate-fade-in">
      {/* Tabs */}
      {files.length > 1 && (
        <div className="flex border-b border-surface-border overflow-x-auto">
          {files.map((f, i) => (
            <button
              key={f.id}
              onClick={() => setActiveTab(i)}
              className={`px-4 py-2 text-xs font-medium whitespace-nowrap transition-colors ${
                i === activeTab
                  ? "text-primary border-b-2 border-primary bg-surface-light/30"
                  : "text-foreground/50 hover:text-foreground/70"
              }`}
            >
              {f.original_name}
            </button>
          ))}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-foreground/80">
            {active.original_name}
          </span>
        </div>
        <span className="text-xs text-foreground/40">
          {formatFileSize(active.file_size)}
        </span>
      </div>

      {/* Content */}
      <div className="max-h-64 overflow-auto p-4">
        <pre className="font-mono text-xs text-foreground/70 leading-relaxed whitespace-pre-wrap break-words">
          {active.preview || "No preview available"}
        </pre>
      </div>
    </div>
  );
}
