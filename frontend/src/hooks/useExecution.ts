"use client";

import { useState, useCallback } from "react";
import * as api from "@/lib/api";
import { useTaskStore } from "@/store/taskStore";
import { toast } from "sonner";

export function useExecution() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const store = useTaskStore();

  const executeScript = useCallback(
    async (taskId: string) => {
      setIsExecuting(true);
      store.setExecuting(true);
      setError(null);
      try {
        const result = await api.executeScript(taskId);
        store.setCurrentTask(result);
        store.updateTask(result);
        if (result.execution_result?.success) {
          toast.success("Script executed successfully!");
        } else {
          toast.error("Script execution failed.");
        }
        return result;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Execution failed";
        setError(msg);
        toast.error(msg);
        return null;
      } finally {
        setIsExecuting(false);
        store.setExecuting(false);
      }
    },
    [store]
  );

  return { isExecuting, error, executeScript };
}
