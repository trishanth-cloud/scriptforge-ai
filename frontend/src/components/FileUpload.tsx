"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Trash2, Loader2 } from "lucide-react";
import { FileResponse, formatFileSize } from "@/lib/types";

interface FileUploadProps {
  files: FileResponse[];
  isUploading: boolean;
  onUpload: (files: File[]) => void;
  onRemove: (fileId: string) => void;
}

const ACCEPTED = {
  "text/plain": [".txt"],
  "text/markdown": [".md"],
  "text/csv": [".csv"],
  "application/json": [".json"],
  "application/xml": [".xml"],
  "text/xml": [".xml"],
  "text/x-log": [".log"],
  "application/x-yaml": [".yaml", ".yml"],
};

export default function FileUpload({
  files,
  isUploading,
  onUpload,
  onRemove,
}: FileUploadProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onUpload(accepted);
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    multiple: true,
    disabled: isUploading,
  });

  return (
    <div className="animate-fade-in">
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragActive
            ? "border-primary bg-primary/10 drop-active"
            : "border-surface-border hover:border-primary/50 hover:bg-surface-light/30"
        } ${isUploading ? "opacity-60 pointer-events-none" : ""}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          {isUploading ? (
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
          ) : (
            <Upload
              className={`w-10 h-10 ${
                isDragActive ? "text-primary" : "text-foreground/30"
              }`}
            />
          )}
          <div>
            <p className="text-sm font-medium text-foreground/80">
              {isDragActive
                ? "Drop files here..."
                : isUploading
                ? "Uploading..."
                : "Drag & drop files here"}
            </p>
            {!isDragActive && !isUploading && (
              <p className="text-xs text-foreground/40 mt-1">
                or{" "}
                <span className="text-primary underline underline-offset-2">
                  browse files
                </span>
              </p>
            )}
          </div>
          <p className="text-[11px] text-foreground/30">
            .txt .md .csv .json .xml .log .yaml .yml
          </p>
        </div>
      </div>

      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((f) => (
            <li
              key={f.id}
              className="flex items-center justify-between bg-surface-light/40 rounded-lg px-4 py-2.5 animate-slide-up"
            >
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="w-4 h-4 text-primary shrink-0" />
                <span className="text-sm text-foreground/80 truncate">
                  {f.original_name}
                </span>
                <span className="text-xs text-foreground/40 shrink-0">
                  {formatFileSize(f.file_size)}
                </span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(f.id);
                }}
                className="text-foreground/30 hover:text-accent-red transition-colors p-1"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
