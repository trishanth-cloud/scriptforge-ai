import { create } from "zustand";
import { TaskResponse, FileResponse } from "@/lib/types";

interface TaskStore {
  currentTask: TaskResponse | null;
  tasks: TaskResponse[];
  uploadedFiles: FileResponse[];
  isUploading: boolean;
  isProcessing: boolean;
  isExecuting: boolean;
  error: string | null;

  setCurrentTask: (task: TaskResponse | null) => void;
  addTask: (task: TaskResponse) => void;
  removeTask: (taskId: string) => void;
  updateTask: (task: TaskResponse) => void;
  setUploadedFiles: (files: FileResponse[]) => void;
  setUploading: (val: boolean) => void;
  setProcessing: (val: boolean) => void;
  setExecuting: (val: boolean) => void;
  setError: (err: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

export const useTaskStore = create<TaskStore>()((set) => ({
  currentTask: null,
  tasks: [],
  uploadedFiles: [],
  isUploading: false,
  isProcessing: false,
  isExecuting: false,
  error: null,

  setCurrentTask: (task) => set({ currentTask: task }),
  addTask: (task) =>
    set((s) => ({ tasks: [task, ...s.tasks] })),
  removeTask: (taskId) =>
    set((s) => ({
      tasks: s.tasks.filter((t) => t.id !== taskId),
      currentTask: s.currentTask?.id === taskId ? null : s.currentTask,
    })),
  updateTask: (task) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === task.id ? task : t)),
      currentTask: s.currentTask?.id === task.id ? task : s.currentTask,
    })),
  setUploadedFiles: (files) => set({ uploadedFiles: files }),
  setUploading: (val) => set({ isUploading: val }),
  setProcessing: (val) => set({ isProcessing: val }),
  setExecuting: (val) => set({ isExecuting: val }),
  setError: (err) => set({ error: err }),
  clearError: () => set({ error: null }),
  reset: () =>
    set({
      currentTask: null,
      tasks: [],
      uploadedFiles: [],
      isUploading: false,
      isProcessing: false,
      isExecuting: false,
      error: null,
    }),
}));
