const API_BASE =
  import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== ""
    ? import.meta.env.VITE_API_BASE_URL
    : (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

export type ApiStatusState =
  | { state: "checking" }
  | { state: "connected" }
  | { state: "unavailable"; reason: string };

export function describeApiTarget(): string {
  if (!API_BASE) {
    return typeof window !== "undefined" ? (window.location.host || "same-origin") : "same-origin";
  }
  try {
    const url = new URL(API_BASE);
    return url.host || API_BASE;
  } catch {
    return API_BASE;
  }
}

export function explainHealthError(err: unknown): string {
  const target = API_BASE || "the backend API";
  if (err instanceof Error) {
    if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
      return `Cannot connect to backend server at ${target}. Make sure the backend server is running.`;
    }
    return err.message;
  }
  return "Unknown connection error";
}

export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error(`Health check failed (${response.status})`);
  return response.json() as Promise<{ status: string; service: string }>;
}

// ── Inventory risk ────────────────────────────────────────────────────────────

export interface BatchRisk {
  batch_id: string;
  batch_code: string;
  product_id: string;
  product_name: string;
  sku: string;
  expiry_date: string;
  quantity_on_hand: number;
  days_to_expiry: number;
  at_risk_units: number;
  risk_percent: number;
  forecast_demand_before_expiry: number;
  insufficient_data: boolean;
}

export async function getRisk(storeId: string): Promise<{ data: BatchRisk[]; message: string | null }> {
  const response = await fetch(`${API_BASE}/api/v1/intelligence/risk?store_id=${encodeURIComponent(storeId)}`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Risk fetch failed (${response.status})`);
  }
  return response.json();
}

export async function recalculate(storeId: string): Promise<{ batches_analyzed: number; forecasts_written: number; recommendations_written: number }> {
  const response = await fetch(`${API_BASE}/api/v1/intelligence/recalculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ store_id: storeId }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Recalculate failed (${response.status})`);
  }
  return response.json();
}

// ── Copilot ───────────────────────────────────────────────────────────────────

export interface CopilotResponse {
  answer: string;
  grounded: boolean;
  context_summary: string;
}

export async function askCopilot(question: string, storeId?: string): Promise<CopilotResponse> {
  const response = await fetch(`${API_BASE}/api/v1/copilot/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, store_id: storeId ?? null }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Copilot request failed (${response.status})`);
  }
  return response.json();
}

// ── CSV ingestion ─────────────────────────────────────────────────────────────

export type DatasetType = "products" | "inventory" | "sales" | "promotions";

export interface ImportError {
  row: number;
  field: string;
  message: string;
}

export interface ImportResult {
  accepted: number;
  rejected: number;
  duplicates: number;
  errors: ImportError[];
  import_id: string;
}

export async function uploadCSV(type: DatasetType, file: File, storeId?: string): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);

  let url = `${API_BASE}/api/v1/ingestion/${type}`;
  if ((type === "inventory" || type === "sales" || type === "promotions") && storeId) {
    url += `?store_id=${encodeURIComponent(storeId)}`;
  }

  const response = await fetch(url, { method: "POST", body: form });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Upload failed (${response.status})`);
  }
  return response.json();
}

export function getSampleCSVUrl(type: DatasetType): string {
  return `${API_BASE}/api/v1/ingestion/${type}/sample`;
}
