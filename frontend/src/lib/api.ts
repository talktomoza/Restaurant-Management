const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("token");
}

export function setToken(token: string) {
  window.localStorage.setItem("token", token);
}

export function clearToken() {
  window.localStorage.removeItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export async function login(email: string, password: string) {
  return request<{ access_token: string; token_type: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string) {
  return request<{ id: number; email: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface Branch {
  id: number;
  name: string;
  location: string;
}

export async function listBranches() {
  return request<Branch[]>("/branches");
}

export async function createBranch(name: string, location: string) {
  return request<Branch>("/branches", {
    method: "POST",
    body: JSON.stringify({ name, location }),
  });
}

export interface ForecastPoint {
  date: string;
  predicted_revenue: number;
  lower_bound: number;
  upper_bound: number;
}

export async function generateForecast(branchId: number, horizonDays = 14) {
  return request<ForecastPoint[]>(`/branches/${branchId}/forecasts?horizon_days=${horizonDays}`, {
    method: "POST",
  });
}

export async function getForecastAccuracy(branchId: number) {
  return request<{ mae_pct: number | null; rmse_pct: number | null }>(
    `/branches/${branchId}/forecasts/accuracy`
  );
}

export interface InventoryAlert {
  sku: string;
  name: string;
  alert_type: string;
  days_to_run_out: number | null;
  current_stock: number;
  suggested_reorder_qty: number;
}

export async function getInventoryAlerts(branchId: number) {
  return request<InventoryAlert[]>(`/branches/${branchId}/inventory-alerts`);
}

export interface ShiftRecommendation {
  shift: string;
  date: string;
  recommended_staff_count: number;
  efficiency_score: number | null;
}

export async function getStaffing(branchId: number, targetDate: string) {
  return request<ShiftRecommendation[]>(
    `/branches/${branchId}/staffing?target_date=${targetDate}`
  );
}

export interface InsightContent {
  summary: string;
  key_risks: string[];
  recommendations: string[];
}

export async function generateWeeklyInsight(branchId: number) {
  return request<InsightContent>(`/branches/${branchId}/insights/weekly-summary`, {
    method: "POST",
  });
}

export interface KpiSummary {
  total_revenue: number;
  order_count: number;
  average_order_value: number;
}

export async function getKpis(branchId: number, startDate: string, endDate: string) {
  return request<KpiSummary>(
    `/branches/${branchId}/dashboard/kpis?start_date=${startDate}&end_date=${endDate}`
  );
}

export interface HeatmapCell {
  day_of_week: number;
  hour: number;
  revenue: number;
}

export async function getHeatmap(branchId: number, startDate: string, endDate: string) {
  return request<HeatmapCell[]>(
    `/branches/${branchId}/dashboard/heatmap?start_date=${startDate}&end_date=${endDate}`
  );
}

export async function uploadCsv(branchId: number, file: File, mapping: Record<string, string>) {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);
  form.append("mapping", JSON.stringify(mapping));
  const res = await fetch(`${API_BASE}/branches/${branchId}/uploads`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<{ rows_imported: number; rows_rejected: number; errors: string[] }>;
}
