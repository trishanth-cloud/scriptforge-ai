"use client";

import { useState, useCallback } from "react";
import * as api from "@/lib/api";
import { FileResponse } from "@/lib/types";
import { useTaskStore } from "@/store/taskStore";
import { toast } from "sonner";

export function useFileUpload() {
  const [files, setFiles] = useState<FileResponse[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const store = useTaskStore();

  const uploadFiles = useCallback(
    async (inputFiles: File[]) => {
      setIsUploading(true);
      store.setUploading(true);
      setError(null);
      try {
        const uploaded = await api.uploadFiles(inputFiles);
        setFiles((prev) => [...prev, ...uploaded]);
        store.setUploadedFiles([...files, ...uploaded]);
        toast.success(
          `${uploaded.length} file${uploaded.length > 1 ? "s" : ""} uploaded`
        );
        return uploaded;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Upload failed";
        setError(msg);
        toast.error(msg);
        return [];
      } finally {
        setIsUploading(false);
        store.setUploading(false);
      }
    },
    [files, store]
  );

  const removeFile = useCallback(
    (fileId: string) => {
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      store.setUploadedFiles(files.filter((f) => f.id !== fileId));
    },
    [files, store]
  );

  const clearFiles = useCallback(() => {
    setFiles([]);
    store.setUploadedFiles([]);
  }, [store]);

  return { files, isUploading, error, uploadFiles, removeFile, clearFiles };
}
