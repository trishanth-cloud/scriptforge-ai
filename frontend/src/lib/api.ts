import {
  FileResponse,
  TaskResponse,
  TaskListResponse,
  ScriptVersion,
  ValidationResult,
} from "./types";

const API_BASE = "/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      ...(options?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
    },
    ...options,
  });

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail || body.message || message;
    } catch {
      // ignore parse error
    }
    throw new ApiError(message, res.status);
  }

  const contentType = res.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res.blob() as unknown as Promise<T>;
}

export async function uploadFiles(files: File[]): Promise<FileResponse[]> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  return request<FileResponse[]>("/files/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getFile(fileId: string): Promise<FileResponse> {
  return request<FileResponse>(`/files/${fileId}`);
}

export async function createTask(fileIds: string[]): Promise<TaskResponse> {
  return request<TaskResponse>("/tasks", {
    method: "POST",
    body: JSON.stringify({ file_ids: fileIds }),
  });
}

export async function listTasks(): Promise<TaskListResponse> {
  return request<TaskListResponse>("/tasks");
}

export async function getTask(taskId: string): Promise<TaskResponse> {
  return request<TaskResponse>(`/tasks/${taskId}`);
}

export async function updateScript(
  taskId: string,
  script: string,
  language?: string
): Promise<TaskResponse> {
  return request<TaskResponse>(`/tasks/${taskId}/script`, {
    method: "PUT",
    body: JSON.stringify({ script, language }),
  });
}

export async function regenerateScript(
  taskId: string
): Promise<TaskResponse> {
  return request<TaskResponse>(`/tasks/${taskId}/regenerate`, {
    method: "POST",
  });
}

export async function validateScript(
  taskId: string
): Promise<ValidationResult> {
  return request<ValidationResult>(`/tasks/${taskId}/validate`, {
    method: "POST",
  });
}

export async function executeScript(
  taskId: string
): Promise<TaskResponse> {
  return request<TaskResponse>(`/tasks/${taskId}/execute`, {
    method: "POST",
    body: JSON.stringify({ approved: true }),
  });
}

export async function downloadScript(taskId: string): Promise<Blob> {
  return request<Blob>(`/tasks/${taskId}/download`);
}

export async function getVersions(
  taskId: string
): Promise<ScriptVersion[]> {
  return request<ScriptVersion[]>(`/tasks/${taskId}/versions`);
}

export async function deleteTask(taskId: string): Promise<void> {
  await request<void>(`/tasks/${taskId}`, { method: "DELETE" });
}

export async function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}
