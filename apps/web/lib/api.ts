import { getAuthHeaders, clearTokens, setTokens } from "./auth";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/** Join the API base URL with a path, avoiding double slashes. */
export function apiUrl(path: string): string {
  const base = API_BASE_URL.replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}

/** Fetch wrapper with auth headers and error handling. */
export async function apiFetch<T>(
  path: string,
  options: RequestInit & { json?: unknown } = {}
): Promise<T> {
  const url = apiUrl(path);
  const { json, ...fetchOpts } = options;
  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  if (json !== undefined) {
    fetchOpts.body = JSON.stringify(json);
  }

  const res = await fetch(url, { ...fetchOpts, headers });

  if (res.status === 401) {
    clearTokens();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const text = await res.text();
    let errorMsg = `API error ${res.status}`;
    try {
      const json = JSON.parse(text);
      errorMsg = json.detail || json.message || errorMsg;
    } catch {
      errorMsg = text || errorMsg;
    }
    const error = new Error(errorMsg);
    (error as any).status = res.status;
    throw error;
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Auth endpoints
export async function login(
  email: string,
  password: string,
  tenant_slug?: string
) {
  const data = await apiFetch<{
    access_token: string;
    refresh_token: string;
    expires_in: number;
  }>("/v1/auth/login", {
    method: "POST",
    json: { email, password, tenant_slug },
  });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function logout() {
  try {
    await apiFetch("/v1/auth/logout", {
      method: "POST",
      json: { refresh_token: "" },
    });
  } catch {
    // Ignore errors during logout
  }
  clearTokens();
}

// Applicant endpoints
export async function createApplicant(email: string) {
  return apiFetch("/v1/applicants", {
    method: "POST",
    json: { email },
  });
}

export async function getApplicant(id: string) {
  return apiFetch(`/v1/applicants/${id}`, { method: "GET" });
}

// Case endpoints
export async function createCase(applicant_id: string, reference?: string) {
  return apiFetch("/v1/onboarding-cases", {
    method: "POST",
    json: { applicant_id, reference },
  });
}

export async function getCase(id: string) {
  return apiFetch(`/v1/onboarding-cases/${id}`, { method: "GET" });
}

export async function listCases(status?: string, limit = 50, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (status) params.append("status", status);
  return apiFetch(`/v1/onboarding-cases?${params.toString()}`, {
    method: "GET",
  });
}

// Consent endpoints
export async function getActiveConsent(case_id: string) {
  return apiFetch(`/v1/consent/active?case_id=${case_id}`, { method: "GET" });
}

export async function recordConsent(case_id: string, notice_id: string) {
  return apiFetch("/v1/consent", {
    method: "POST",
    json: { case_id, notice_id, accepted: true },
  });
}

// Document endpoints
export async function uploadDocument(case_id: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("case_id", case_id);
  return apiFetch("/v1/documents", {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
  });
}

export async function getDocument(id: string) {
  return apiFetch(`/v1/documents/${id}`, { method: "GET" });
}

export async function getRedactedDocument(id: string) {
  return apiFetch(`/v1/documents/${id}/redacted`, { method: "GET" });
}

// Risk endpoints
export async function getRiskDecision(case_id: string) {
  return apiFetch(`/v1/risk/decisions?case_id=${case_id}`, { method: "GET" });
}

// Review endpoints
export async function listReviewTasks(status?: string, limit = 50, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (status) params.append("status", status);
  return apiFetch(`/v1/review/tasks?${params.toString()}`, { method: "GET" });
}

export async function getReviewTask(id: string) {
  return apiFetch(`/v1/review/tasks/${id}`, { method: "GET" });
}

export async function resolveReviewTask(id: string, decision: string, notes?: string) {
  return apiFetch(`/v1/review/tasks/${id}/resolve`, {
    method: "POST",
    json: { decision, notes },
  });
}

// Audit endpoints
export async function listAuditEvents(limit = 100, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiFetch(`/v1/audit-events?${params.toString()}`, { method: "GET" });
}

// Webhook endpoints
export async function listWebhookEndpoints() {
  return apiFetch("/v1/webhooks/endpoints", { method: "GET" });
}

export async function createWebhookEndpoint(url: string, event_types: string[]) {
  return apiFetch("/v1/webhooks/endpoints", {
    method: "POST",
    json: { url, event_types, active: true },
  });
}

export async function getWebhookEndpoint(id: string) {
  return apiFetch(`/v1/webhooks/endpoints/${id}`, { method: "GET" });
}

export async function deleteWebhookEndpoint(id: string) {
  return apiFetch(`/v1/webhooks/endpoints/${id}`, { method: "DELETE" });
}

// Health endpoint
export async function getHealth() {
  return apiFetch("/health", { method: "GET" });
}
