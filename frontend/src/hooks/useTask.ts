"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import * as api from "@/lib/api";
import { TaskResponse, isProcessing, TaskStatus } from "@/lib/types";
import { useTaskStore } from "@/store/taskStore";
import { toast } from "sonner";

export function useTask() {
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const store = useTaskStore();

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const refreshTask = useCallback(
    async (taskId: string) => {
      try {
        const updated = await api.getTask(taskId);
        setTask(updated);
        store.setCurrentTask(updated);
        store.updateTask(updated);
        return updated;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Failed to fetch task";
        setError(msg);
        return null;
      }
    },
    [store]
  );

  const startPolling = useCallback(
    (taskId: string) => {
      stopPolling();
      intervalRef.current = setInterval(async () => {
        const updated = await refreshTask(taskId);
        if (updated && !isProcessing(updated.status)) {
          stopPolling();
          store.setProcessing(false);
          if (updated.status === TaskStatus.COMPLETED) {
            toast.success("Script generation completed!");
          } else if (
            updated.status === TaskStatus.FAILED ||
            updated.status === TaskStatus.ERROR
          ) {
            toast.error("Task failed. Check the results for details.");
          }
        }
      }, 2000);
    },
    [refreshTask, stopPolling, store]
  );

  const createTask = useCallback(
    async (fileIds: string[]) => {
      setIsLoading(true);
      setError(null);
      store.setProcessing(true);
      try {
        const created = await api.createTask(fileIds);
        setTask(created);
        store.setCurrentTask(created);
        store.addTask(created);
        toast.success("Task created — analyzing files...");
        startPolling(created.id);
        return created;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Failed to create task";
        setError(msg);
        store.setProcessing(false);
        toast.error(msg);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [store, startPolling]
  );

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  return { task, isLoading, error, createTask, refreshTask, startPolling };
}
