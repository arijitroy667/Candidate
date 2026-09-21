const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type ApiResponse<T> = { data: T; meta?: Record<string, unknown> };
export type Job = { id: string; title: string; description: string; company_id: string; location?: string; employment_type?: string; skills: string[]; status: string };
export type Application = { id: string; job_id: string; status: string; created_at: string };

export async function apiFetch<T>(path: string, options: RequestInit = {}, accessToken?: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
  });
  const payload = (await response.json()) as ApiResponse<T> | { detail?: string };
  if (!response.ok) {
    throw new Error("detail" in payload && payload.detail ? payload.detail : "Request failed");
  }
  return (payload as ApiResponse<T>).data;
}

export const api = {
  health: () => apiFetch<{ status: string; service: string }>("/health"),
  publicJobs: () => apiFetch<Job[]>("/public/jobs"),
  publicJob: (id: string) => apiFetch<Job>(`/public/jobs/${id}`),
  applications: (token: string) => apiFetch<Application[]>("/applications", {}, token),
  companyJobs: (token: string) => apiFetch<Job[]>("/jobs", {}, token),
  notifications: (token: string, unreadOnly = false) =>
    apiFetch<unknown[]>(`/notifications?unread_only=${unreadOnly}`, {}, token),
  markNotificationRead: (token: string, id: string) =>
    apiFetch<unknown>(`/notifications/${id}`, { method: "PATCH", body: JSON.stringify({ is_read: true }) }, token),
};
