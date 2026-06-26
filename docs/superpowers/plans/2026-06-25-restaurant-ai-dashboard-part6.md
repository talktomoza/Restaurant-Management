# AI-Powered Restaurant Analytics Dashboard Implementation Plan — Part 6 (Tasks 19-26, final)

> Continuation of Parts 1-5. Same Global Constraints apply. This part completes the plan.

---

## Task 19: Next.js scaffolding + API client + types

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/auth.ts`
- Create: `frontend/lib/api.ts`
- Create: `frontend/.env.local.example`
- Test: `frontend/tests/api.test.ts`

**Interfaces:**
- Produces: `frontend/lib/types.ts` — TypeScript interfaces mirroring backend Pydantic schemas: `Branch`, `KpiSummary`, `HeatmapCell`, `ForecastPoint`, `InventoryAlert`, `ShiftRecommendation`, `InsightContent`.
- Produces: `frontend/lib/auth.ts` — `getToken(): string | null`, `setToken(token: string): void`, `clearToken(): void` (using `localStorage`).
- Produces: `frontend/lib/api.ts` — `apiFetch<T>(path: string, options?: RequestInit): Promise<T>` that prefixes `process.env.NEXT_PUBLIC_API_URL`, attaches `Authorization: Bearer {token}` header when a token exists, throws an `Error` with the response body's `detail` field on non-2xx responses.

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "restaurant-dashboard-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run"
  },
  "dependencies": {
    "next": "15.1.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "recharts": "2.13.3"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "6.6.3",
    "@testing-library/react": "16.1.0",
    "@types/node": "22.10.2",
    "@types/react": "19.0.2",
    "@types/react-dom": "19.0.2",
    "@vitejs/plugin-react": "4.3.4",
    "autoprefixer": "10.4.20",
    "jsdom": "25.0.1",
    "postcss": "8.4.49",
    "tailwindcss": "3.4.17",
    "typescript": "5.7.2",
    "vitest": "2.1.8"
  }
}
```

- [ ] **Step 2: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": { "@/*": ["./*"] }
  },
  "include": ["**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Create `frontend/next.config.mjs`, `frontend/tailwind.config.ts`, `frontend/postcss.config.mjs`**

```javascript
// frontend/next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {};
export default nextConfig;
```

```typescript
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
export default config;
```

```javascript
// frontend/postcss.config.mjs
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
```

- [ ] **Step 4: Create `frontend/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 5: Create `frontend/app/layout.tsx`**

```tsx
// frontend/app/layout.tsx
import "./globals.css";

export const metadata = {
  title: "Restaurant Analytics Dashboard",
  description: "AI-powered restaurant analytics and forecasting",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
```

- [ ] **Step 6: Create `frontend/lib/types.ts`**

```typescript
// frontend/lib/types.ts
export interface Branch {
  id: number;
  name: string;
  location: string | null;
}

export interface KpiSummary {
  total_revenue: number;
  order_count: number;
  average_order_value: number;
}

export interface HeatmapCell {
  day_of_week: number;
  hour: number;
  revenue: number;
}

export interface ForecastPoint {
  date: string;
  predicted_revenue: number;
  lower_bound: number;
  upper_bound: number;
}

export interface InventoryAlert {
  sku: string;
  name: string;
  alert_type: "stockout_risk" | "overstock";
  days_to_run_out: number | null;
  current_stock: number;
  suggested_reorder_qty: number;
}

export interface ShiftRecommendation {
  shift: "morning" | "afternoon" | "evening";
  date: string;
  recommended_staff_count: number;
  efficiency_score: number | null;
}

export interface InsightContent {
  summary: string;
  key_risks: string[];
  recommendations: string[];
}
```

- [ ] **Step 7: Create `frontend/lib/auth.ts`**

```typescript
// frontend/lib/auth.ts
const TOKEN_KEY = "restaurant_dashboard_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}
```

- [ ] **Step 8: Create `frontend/.env.local.example`**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 9: Write the failing test for the API client**

```typescript
// frontend/tests/api.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiFetch } from "../lib/api";
import { setToken, clearToken } from "../lib/auth";

describe("apiFetch", () => {
  beforeEach(() => {
    clearToken();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("attaches Authorization header when a token is set", async () => {
    setToken("abc123");
    (fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ result: "ok" }),
    });

    const result = await apiFetch<{ result: string }>("/health");

    expect(result.result).toBe("ok");
    const [, options] = (fetch as any).mock.calls[0];
    expect(options.headers.Authorization).toBe("Bearer abc123");
  });

  it("throws with the response detail on non-2xx status", async () => {
    (fetch as any).mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Not found" }),
    });

    await expect(apiFetch("/missing")).rejects.toThrow("Not found");
  });
});
```

- [ ] **Step 10: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/api.test.ts`
Expected: FAIL with module not found (`lib/api` doesn't exist yet)

- [ ] **Step 11: Create `frontend/lib/api.ts`**

```typescript
// frontend/lib/api.ts
import { getToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  const body = await response.json();

  if (!response.ok) {
    throw new Error(body.detail || "Request failed");
  }
  return body as T;
}
```

- [ ] **Step 12: Create `frontend/vitest.config.ts`**

```typescript
// frontend/vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

- [ ] **Step 13: Install dependencies and run the test**

Run: `cd frontend && npm install`
Expected: Installs without errors.

Run: `cd frontend && npx vitest run tests/api.test.ts`
Expected: PASS (2 tests)

- [ ] **Step 14: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/next.config.mjs frontend/tailwind.config.ts frontend/postcss.config.mjs frontend/vitest.config.ts frontend/app/globals.css frontend/app/layout.tsx frontend/lib frontend/.env.local.example frontend/tests/api.test.ts
git commit -m "Scaffold Next.js frontend with typed API client and auth token storage"
```

Note: do not commit `frontend/package-lock.json` exclusion — it SHOULD be committed (already not in `.gitignore`); only `node_modules/` is excluded.

---

## Task 20: Login page

**Files:**
- Create: `frontend/app/login/page.tsx`
- Test: `frontend/tests/LoginPage.test.tsx`

**Interfaces:**
- Consumes: `apiFetch` from Task 19, `setToken` from `lib/auth.ts`.
- Produces: a client component at `/login` with email/password fields, a submit handler that POSTs to `/auth/login`, stores the token via `setToken`, and redirects to `/` on success; shows an inline error message on failure.

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/tests/LoginPage.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "../app/login/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("shows an error message when login fails", async () => {
    (fetch as any).mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Incorrect email or password" }),
    });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "a@example.com" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => {
      expect(screen.getByText(/incorrect email or password/i)).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/LoginPage.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Create `frontend/app/login/page.tsx`**

```tsx
// frontend/app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const result = await apiFetch<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(result.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4 rounded-lg bg-white p-8 shadow">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <div>
          <label htmlFor="email" className="block text-sm font-medium">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2"
            required
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2"
            required
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" className="w-full rounded bg-slate-900 py-2 text-white">
          Log in
        </button>
      </form>
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run tests/LoginPage.test.tsx`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add frontend/app/login frontend/tests/LoginPage.test.tsx
git commit -m "Add login page with token storage and error handling"
```

---

## Task 21: KPI cards + branch/date filter components

**Files:**
- Create: `frontend/components/KpiCard.tsx`
- Create: `frontend/components/BranchDateFilter.tsx`
- Test: `frontend/tests/KpiCard.test.tsx`

**Interfaces:**
- Produces: `KpiCard({ label, value, format }: { label: string; value: number; format?: "currency" | "number" })` — pure presentational component rendering `label` and a formatted `value`.
- Produces: `BranchDateFilter({ branches, selectedBranchId, startDate, endDate, onChange }: { branches: Branch[]; selectedBranchId: number | null; startDate: string; endDate: string; onChange: (next: { branchId: number; startDate: string; endDate: string }) => void })` — renders a branch `<select>` and two date inputs, calling `onChange` on any field change.

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/tests/KpiCard.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import KpiCard from "../components/KpiCard";

describe("KpiCard", () => {
  it("renders a currency-formatted value", () => {
    render(<KpiCard label="Total Revenue" value={1234.5} format="currency" />);
    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$1,234.50")).toBeInTheDocument();
  });

  it("renders a plain number value by default", () => {
    render(<KpiCard label="Order Count" value={42} />);
    expect(screen.getByText("42")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/KpiCard.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Create `frontend/components/KpiCard.tsx`**

```tsx
// frontend/components/KpiCard.tsx
interface KpiCardProps {
  label: string;
  value: number;
  format?: "currency" | "number";
}

export default function KpiCard({ label, value, format = "number" }: KpiCardProps) {
  const formatted =
    format === "currency"
      ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value)
      : new Intl.NumberFormat("en-US").format(value);

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{formatted}</p>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run tests/KpiCard.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 5: Create `frontend/components/BranchDateFilter.tsx` (no dedicated test — covered by dashboard integration in Task 24)**

```tsx
// frontend/components/BranchDateFilter.tsx
import type { Branch } from "@/lib/types";

interface BranchDateFilterProps {
  branches: Branch[];
  selectedBranchId: number | null;
  startDate: string;
  endDate: string;
  onChange: (next: { branchId: number; startDate: string; endDate: string }) => void;
}

export default function BranchDateFilter({
  branches,
  selectedBranchId,
  startDate,
  endDate,
  onChange,
}: BranchDateFilterProps) {
  return (
    <div className="flex flex-wrap items-end gap-4">
      <div>
        <label className="block text-sm font-medium">Branch</label>
        <select
          value={selectedBranchId ?? ""}
          onChange={(e) => onChange({ branchId: Number(e.target.value), startDate, endDate })}
          className="mt-1 rounded border px-3 py-2"
        >
          {branches.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium">Start date</label>
        <input
          type="date"
          value={startDate}
          onChange={(e) =>
            onChange({ branchId: selectedBranchId ?? 0, startDate: e.target.value, endDate })
          }
          className="mt-1 rounded border px-3 py-2"
        />
      </div>
      <div>
        <label className="block text-sm font-medium">End date</label>
        <input
          type="date"
          value={endDate}
          onChange={(e) =>
            onChange({ branchId: selectedBranchId ?? 0, startDate, endDate: e.target.value })
          }
          className="mt-1 rounded border px-3 py-2"
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/components/KpiCard.tsx frontend/components/BranchDateFilter.tsx frontend/tests/KpiCard.test.tsx
git commit -m "Add KPI card and branch/date filter components"
```

---

## Task 22: Forecast chart + Peak-hour heatmap components

**Files:**
- Create: `frontend/components/ForecastChart.tsx`
- Create: `frontend/components/PeakHourHeatmap.tsx`
- Test: `frontend/tests/ForecastChart.test.tsx`

**Interfaces:**
- Produces: `ForecastChart({ data }: { data: ForecastPoint[] })` — renders a Recharts `ComposedChart` with a shaded area between `lower_bound`/`upper_bound` and a line for `predicted_revenue`; renders a "No forecast data yet" message when `data` is empty.
- Produces: `PeakHourHeatmap({ cells }: { cells: HeatmapCell[] })` — renders a 7x24 grid, cell background intensity scaled by `revenue` relative to the max value in `cells`; renders "No data for this range" when `cells` is empty.

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/tests/ForecastChart.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ForecastChart from "../components/ForecastChart";

describe("ForecastChart", () => {
  it("shows an empty state when there is no data", () => {
    render(<ForecastChart data={[]} />);
    expect(screen.getByText(/no forecast data yet/i)).toBeInTheDocument();
  });

  it("renders a chart container when data is present", () => {
    render(
      <ForecastChart
        data={[
          { date: "2026-03-01", predicted_revenue: 100, lower_bound: 90, upper_bound: 110 },
        ]}
      />
    );
    expect(screen.queryByText(/no forecast data yet/i)).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/ForecastChart.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Create `frontend/components/ForecastChart.tsx`**

```tsx
// frontend/components/ForecastChart.tsx
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import type { ForecastPoint } from "@/lib/types";

export default function ForecastChart({ data }: { data: ForecastPoint[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-slate-500">No forecast data yet.</p>;
  }

  return (
    <div className="h-72 w-full" data-testid="forecast-chart">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Area
            dataKey="upper_bound"
            stroke="none"
            fill="#cbd5e1"
            fillOpacity={0.5}
            isAnimationActive={false}
          />
          <Area
            dataKey="lower_bound"
            stroke="none"
            fill="#ffffff"
            fillOpacity={1}
            isAnimationActive={false}
          />
          <Line dataKey="predicted_revenue" stroke="#0f172a" strokeWidth={2} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run tests/ForecastChart.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 5: Create `frontend/components/PeakHourHeatmap.tsx` (no dedicated test — visual component, covered manually in Task 24's E2E check)**

```tsx
// frontend/components/PeakHourHeatmap.tsx
import type { HeatmapCell } from "@/lib/types";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function PeakHourHeatmap({ cells }: { cells: HeatmapCell[] }) {
  if (cells.length === 0) {
    return <p className="text-sm text-slate-500">No data for this range.</p>;
  }

  const maxRevenue = Math.max(...cells.map((c) => c.revenue));
  const lookup = new Map(cells.map((c) => [`${c.day_of_week}-${c.hour}`, c.revenue]));

  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-1"></th>
            {HOURS.map((h) => (
              <th key={h} className="p-1 text-slate-400">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {DAYS.map((day, dow) => (
            <tr key={day}>
              <td className="p-1 font-medium text-slate-500">{day}</td>
              {HOURS.map((hour) => {
                const revenue = lookup.get(`${dow}-${hour}`) ?? 0;
                const intensity = maxRevenue > 0 ? revenue / maxRevenue : 0;
                return (
                  <td key={hour} className="p-0">
                    <div
                      className="h-5 w-5"
                      style={{ backgroundColor: `rgba(15, 23, 42, ${intensity})` }}
                      title={`${day} ${hour}:00 — $${revenue.toFixed(2)}`}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/components/ForecastChart.tsx frontend/components/PeakHourHeatmap.tsx frontend/tests/ForecastChart.test.tsx
git commit -m "Add forecast chart and peak-hour heatmap components"
```

---

## Task 23: Inventory panel, Staffing panel, Insight panel components

**Files:**
- Create: `frontend/components/InventoryPanel.tsx`
- Create: `frontend/components/StaffingPanel.tsx`
- Create: `frontend/components/InsightPanel.tsx`
- Test: `frontend/tests/InsightPanel.test.tsx`

**Interfaces:**
- Produces: `InventoryPanel({ alerts }: { alerts: InventoryAlert[] })` — list of alert rows, color-coded by `alert_type` (red for `stockout_risk`, amber for `overstock`); "No inventory alerts" empty state.
- Produces: `StaffingPanel({ recommendations }: { recommendations: ShiftRecommendation[] })` — table of shift → recommended count → efficiency score; "No staffing data" empty state.
- Produces: `InsightPanel({ insight, loading }: { insight: InsightContent | null; loading: boolean })` — shows a loading skeleton when `loading`, the structured summary/risks/recommendations when `insight` is set, and "No insight generated yet" otherwise.

- [ ] **Step 1: Write the failing test for InsightPanel (most state-dependent component)**

```tsx
// frontend/tests/InsightPanel.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import InsightPanel from "../components/InsightPanel";

describe("InsightPanel", () => {
  it("shows a loading state", () => {
    render(<InsightPanel insight={null} loading={true} />);
    expect(screen.getByText(/generating insight/i)).toBeInTheDocument();
  });

  it("shows the empty state when there is no insight and not loading", () => {
    render(<InsightPanel insight={null} loading={false} />);
    expect(screen.getByText(/no insight generated yet/i)).toBeInTheDocument();
  });

  it("renders the insight content when present", () => {
    render(
      <InsightPanel
        insight={{
          summary: "Revenue is up.",
          key_risks: ["Low stock on buns."],
          recommendations: ["Reorder buns."],
        }}
        loading={false}
      />
    );
    expect(screen.getByText("Revenue is up.")).toBeInTheDocument();
    expect(screen.getByText("Low stock on buns.")).toBeInTheDocument();
    expect(screen.getByText("Reorder buns.")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/InsightPanel.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Create `frontend/components/InsightPanel.tsx`**

```tsx
// frontend/components/InsightPanel.tsx
import type { InsightContent } from "@/lib/types";

interface InsightPanelProps {
  insight: InsightContent | null;
  loading: boolean;
}

export default function InsightPanel({ insight, loading }: InsightPanelProps) {
  if (loading) {
    return <p className="text-sm text-slate-500">Generating insight...</p>;
  }

  if (!insight) {
    return <p className="text-sm text-slate-500">No insight generated yet.</p>;
  }

  return (
    <div className="space-y-3">
      <p className="text-base">{insight.summary}</p>
      <div>
        <h3 className="text-sm font-semibold text-red-700">Key Risks</h3>
        <ul className="list-disc pl-5 text-sm">
          {insight.key_risks.map((risk) => (
            <li key={risk}>{risk}</li>
          ))}
        </ul>
      </div>
      <div>
        <h3 className="text-sm font-semibold text-emerald-700">Recommendations</h3>
        <ul className="list-disc pl-5 text-sm">
          {insight.recommendations.map((rec) => (
            <li key={rec}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run tests/InsightPanel.test.tsx`
Expected: PASS (3 tests)

- [ ] **Step 5: Create `frontend/components/InventoryPanel.tsx` (no dedicated test — simple list rendering, covered manually)**

```tsx
// frontend/components/InventoryPanel.tsx
import type { InventoryAlert } from "@/lib/types";

export default function InventoryPanel({ alerts }: { alerts: InventoryAlert[] }) {
  if (alerts.length === 0) {
    return <p className="text-sm text-slate-500">No inventory alerts.</p>;
  }

  return (
    <ul className="space-y-2">
      {alerts.map((alert) => (
        <li
          key={alert.sku}
          className={`rounded p-2 text-sm ${
            alert.alert_type === "stockout_risk" ? "bg-red-50 text-red-800" : "bg-amber-50 text-amber-800"
          }`}
        >
          <span className="font-medium">{alert.name}</span> — {alert.alert_type === "stockout_risk"
            ? `Stockout risk in ${alert.days_to_run_out} days. Reorder ${alert.suggested_reorder_qty} units.`
            : `Overstocked (${alert.days_to_run_out} days of supply).`}
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 6: Create `frontend/components/StaffingPanel.tsx` (no dedicated test — simple table rendering, covered manually)**

```tsx
// frontend/components/StaffingPanel.tsx
import type { ShiftRecommendation } from "@/lib/types";

export default function StaffingPanel({ recommendations }: { recommendations: ShiftRecommendation[] }) {
  if (recommendations.length === 0) {
    return <p className="text-sm text-slate-500">No staffing data.</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-slate-500">
          <th className="py-1">Shift</th>
          <th className="py-1">Recommended Staff</th>
          <th className="py-1">Efficiency</th>
        </tr>
      </thead>
      <tbody>
        {recommendations.map((rec) => (
          <tr key={rec.shift} className="border-t">
            <td className="py-1 capitalize">{rec.shift}</td>
            <td className="py-1">{rec.recommended_staff_count}</td>
            <td className="py-1">{rec.efficiency_score !== null ? `${rec.efficiency_score}%` : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/components/InventoryPanel.tsx frontend/components/StaffingPanel.tsx frontend/components/InsightPanel.tsx frontend/tests/InsightPanel.test.tsx
git commit -m "Add inventory, staffing, and AI insight panel components"
```

---

## Task 24: CSV upload wizard component + upload page

**Files:**
- Create: `frontend/components/CsvUploadWizard.tsx`
- Create: `frontend/app/upload/page.tsx`
- Test: `frontend/tests/CsvUploadWizard.test.tsx`

**Interfaces:**
- Produces: `CsvUploadWizard({ branchId, onComplete }: { branchId: number; onComplete: (result: { rows_imported: number; rows_rejected: number }) => void })` — two-step wizard: (1) file picker that reads the CSV header row client-side to populate column-mapping dropdowns, (2) mapping form (date/item/quantity/amount columns) that submits via `FormData` to `POST /branches/{branchId}/uploads`.

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/tests/CsvUploadWizard.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import CsvUploadWizard from "../components/CsvUploadWizard";

function makeFile(content: string, name = "sales.csv") {
  return new File([content], name, { type: "text/csv" });
}

describe("CsvUploadWizard", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("parses header columns from the selected file and shows mapping selects", async () => {
    render(<CsvUploadWizard branchId={1} onComplete={vi.fn()} />);

    const file = makeFile("Date,Item,Qty,Total\n2026-01-01,Burger,1,9.99\n");
    const input = screen.getByLabelText(/csv file/i);
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByLabelText(/date column/i)).toBeInTheDocument();
    });
    const dateSelect = screen.getByLabelText(/date column/i) as HTMLSelectElement;
    const options = Array.from(dateSelect.options).map((o) => o.value);
    expect(options).toContain("Date");
    expect(options).toContain("Total");
  });

  it("calls onComplete with the upload result after a successful submit", async () => {
    (fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ rows_imported: 1, rows_rejected: 0, errors: [] }),
    });
    const onComplete = vi.fn();

    render(<CsvUploadWizard branchId={1} onComplete={onComplete} />);

    const file = makeFile("Date,Item,Qty,Total\n2026-01-01,Burger,1,9.99\n");
    fireEvent.change(screen.getByLabelText(/csv file/i), { target: { files: [file] } });
    await waitFor(() => expect(screen.getByLabelText(/date column/i)).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /upload/i }));

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith({ rows_imported: 1, rows_rejected: 0 });
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/CsvUploadWizard.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Create `frontend/components/CsvUploadWizard.tsx`**

```tsx
// frontend/components/CsvUploadWizard.tsx
"use client";

import { useState } from "react";
import { getToken } from "@/lib/auth";

interface CsvUploadWizardProps {
  branchId: number;
  onComplete: (result: { rows_imported: number; rows_rejected: number }) => void;
}

const FIELDS = [
  { key: "date_column", label: "Date column" },
  { key: "item_column", label: "Item column" },
  { key: "quantity_column", label: "Quantity column" },
  { key: "amount_column", label: "Amount column" },
] as const;

export default function CsvUploadWizard({ branchId, onComplete }: CsvUploadWizardProps) {
  const [file, setFile] = useState<File | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setError(null);
    if (!selected) return;

    const text = await selected.text();
    const headerLine = text.split("\n")[0] ?? "";
    const parsedColumns = headerLine.split(",").map((c) => c.trim()).filter(Boolean);
    setColumns(parsedColumns);
    setMapping({});
  }

  async function handleUpload() {
    if (!file) return;
    setError(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const formData = new FormData();
    formData.append("file", file);
    formData.append("mapping", JSON.stringify(mapping));

    const token = getToken();
    const response = await fetch(`${apiUrl}/branches/${branchId}/uploads`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: formData,
    });

    const body = await response.json();
    if (!response.ok) {
      setError(body.detail?.errors?.join(", ") || "Upload failed");
      return;
    }
    onComplete({ rows_imported: body.rows_imported, rows_rejected: body.rows_rejected });
  }

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="csv-file" className="block text-sm font-medium">CSV file</label>
        <input id="csv-file" type="file" accept=".csv" onChange={handleFileChange} className="mt-1" />
      </div>

      {columns.length > 0 && (
        <div className="space-y-3">
          {FIELDS.map(({ key, label }) => (
            <div key={key}>
              <label htmlFor={key} className="block text-sm font-medium">{label}</label>
              <select
                id={key}
                aria-label={label}
                value={mapping[key] ?? ""}
                onChange={(e) => setMapping({ ...mapping, [key]: e.target.value })}
                className="mt-1 rounded border px-3 py-2"
              >
                <option value="">Select column</option>
                {columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </div>
          ))}
          <button
            type="button"
            onClick={handleUpload}
            className="rounded bg-slate-900 px-4 py-2 text-white"
          >
            Upload
          </button>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run tests/CsvUploadWizard.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 5: Create `frontend/app/upload/page.tsx`**

```tsx
// frontend/app/upload/page.tsx
"use client";

import { useState } from "react";
import CsvUploadWizard from "@/components/CsvUploadWizard";

export default function UploadPage() {
  const [result, setResult] = useState<{ rows_imported: number; rows_rejected: number } | null>(null);

  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="mb-4 text-xl font-semibold">Upload Sales Data</h1>
      <CsvUploadWizard branchId={1} onComplete={setResult} />
      {result && (
        <p className="mt-4 text-sm text-emerald-700">
          Imported {result.rows_imported} rows ({result.rows_rejected} rejected).
        </p>
      )}
    </main>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/components/CsvUploadWizard.tsx frontend/app/upload frontend/tests/CsvUploadWizard.test.tsx
git commit -m "Add CSV upload wizard with client-side column detection"
```

---

## Task 25: Dashboard page (wires all components together)

**Files:**
- Create: `frontend/app/page.tsx`
- Test: manual verification (covered by component-level tests already written; this task is integration wiring)

**Interfaces:**
- Consumes: every component from Tasks 21-23, `apiFetch` from Task 19, types from Task 19.
- Produces: `frontend/app/page.tsx` — a client component that on mount fetches branches, defaults to the first branch and a 30-day date range, then fetches KPIs/heatmap/forecast/inventory/staffing/insight for the selected branch+range, re-fetching whenever the filter changes. Redirects to `/login` if no auth token is present.

- [ ] **Step 1: Create `frontend/app/page.tsx`**

```tsx
// frontend/app/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type {
  Branch, KpiSummary, HeatmapCell, ForecastPoint, InventoryAlert, ShiftRecommendation, InsightContent,
} from "@/lib/types";
import KpiCard from "@/components/KpiCard";
import BranchDateFilter from "@/components/BranchDateFilter";
import PeakHourHeatmap from "@/components/PeakHourHeatmap";
import ForecastChart from "@/components/ForecastChart";
import InventoryPanel from "@/components/InventoryPanel";
import StaffingPanel from "@/components/StaffingPanel";
import InsightPanel from "@/components/InsightPanel";

function defaultDateRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 30);
  return { startDate: start.toISOString().slice(0, 10), endDate: end.toISOString().slice(0, 10) };
}

export default function DashboardPage() {
  const router = useRouter();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchId, setBranchId] = useState<number | null>(null);
  const [{ startDate, endDate }, setRange] = useState(defaultDateRange());
  const [kpis, setKpis] = useState<KpiSummary | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapCell[]>([]);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [inventoryAlerts, setInventoryAlerts] = useState<InventoryAlert[]>([]);
  const [staffing, setStaffing] = useState<ShiftRecommendation[]>([]);
  const [insight, setInsight] = useState<InsightContent | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    apiFetch<Branch[]>("/branches").then((data) => {
      setBranches(data);
      if (data.length > 0) setBranchId(data[0].id);
    });
  }, [router]);

  useEffect(() => {
    if (!branchId) return;

    apiFetch<KpiSummary>(
      `/branches/${branchId}/dashboard/kpis?start_date=${startDate}&end_date=${endDate}`
    ).then(setKpis);

    apiFetch<HeatmapCell[]>(
      `/branches/${branchId}/dashboard/heatmap?start_date=${startDate}&end_date=${endDate}`
    ).then(setHeatmap);

    apiFetch<InventoryAlert[]>(`/branches/${branchId}/inventory-alerts`).then(setInventoryAlerts);

    apiFetch<ShiftRecommendation[]>(
      `/branches/${branchId}/staffing?target_date=${endDate}`
    ).then(setStaffing).catch(() => setStaffing([]));

    setInsightLoading(true);
    apiFetch<InsightContent>(`/branches/${branchId}/insights/weekly-summary`, { method: "POST" })
      .then(setInsight)
      .catch(() => setInsight(null))
      .finally(() => setInsightLoading(false));
  }, [branchId, startDate, endDate]);

  useEffect(() => {
    if (!branchId) return;
    apiFetch<ForecastPoint[]>(`/branches/${branchId}/forecasts?horizon_days=7`, { method: "POST" })
      .then(setForecast)
      .catch(() => setForecast([]));
  }, [branchId]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-8">
      <h1 className="text-2xl font-semibold">Restaurant Analytics Dashboard</h1>

      <BranchDateFilter
        branches={branches}
        selectedBranchId={branchId}
        startDate={startDate}
        endDate={endDate}
        onChange={({ branchId: nextBranchId, startDate: s, endDate: e }) => {
          setBranchId(nextBranchId);
          setRange({ startDate: s, endDate: e });
        }}
      />

      {kpis && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <KpiCard label="Total Revenue" value={kpis.total_revenue} format="currency" />
          <KpiCard label="Order Count" value={kpis.order_count} />
          <KpiCard label="Average Order Value" value={kpis.average_order_value} format="currency" />
        </div>
      )}

      <section className="rounded-lg bg-white p-4 shadow">
        <h2 className="mb-2 text-lg font-medium">Peak Hours</h2>
        <PeakHourHeatmap cells={heatmap} />
      </section>

      <section className="rounded-lg bg-white p-4 shadow">
        <h2 className="mb-2 text-lg font-medium">7-Day Revenue Forecast</h2>
        <ForecastChart data={forecast} />
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <section className="rounded-lg bg-white p-4 shadow">
          <h2 className="mb-2 text-lg font-medium">Inventory Alerts</h2>
          <InventoryPanel alerts={inventoryAlerts} />
        </section>
        <section className="rounded-lg bg-white p-4 shadow">
          <h2 className="mb-2 text-lg font-medium">Staffing</h2>
          <StaffingPanel recommendations={staffing} />
        </section>
      </div>

      <section className="rounded-lg bg-white p-4 shadow">
        <h2 className="mb-2 text-lg font-medium">AI Insight</h2>
        <InsightPanel insight={insight} loading={insightLoading} />
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Run the full frontend test suite to confirm nothing broke**

Run: `cd frontend && npx vitest run`
Expected: All PASS

- [ ] **Step 3: Manual browser verification**

Run: `cd frontend && npm run dev` (with backend also running per Task 18, and at least one branch + uploaded CSV + generated forecast/inventory items created via API or future seed step)
Expected: Visiting `http://localhost:3000` (after logging in at `/login`) shows the dashboard with KPI cards, heatmap, forecast chart, inventory/staffing panels, and AI insight panel without console errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/page.tsx
git commit -m "Wire dashboard page integrating all KPI, forecast, inventory, staffing, and insight components"
```

---

## Task 26: Frontend Dockerfile, docker-compose integration, and README

**Files:**
- Create: `frontend/Dockerfile`
- Modify: `docker-compose.yml`
- Create: `README.md`

**Interfaces:**
- Produces: `frontend/Dockerfile` — multi-stage Node build (`node:20-slim`), builds with `npm run build`, serves with `npm start`.
- Modifies: `docker-compose.yml` to add a `frontend` service depending on `backend`.
- Produces: `README.md` covering project description, architecture diagram (ASCII), setup instructions (Docker Compose and manual), environment variables, API overview, forecast accuracy metrics location, known limitations, and how to run tests.

- [ ] **Step 1: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3000
CMD ["npm", "start"]
```

- [ ] **Step 2: Update `docker-compose.yml` to add the frontend service**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: restaurant
      POSTGRES_PASSWORD: restaurant
      POSTGRES_DB: restaurant_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U restaurant"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - backend/.env
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

- [ ] **Step 3: Create `README.md`**

```markdown
# AI-Powered Restaurant Analytics Dashboard

End-to-end restaurant analytics platform: CSV ingestion, Prophet-based revenue
forecasting, inventory intelligence, staffing recommendations, and an LLM
(DeepSeek via OpenRouter) insight layer, surfaced through a multi-branch
Next.js dashboard backed by a FastAPI + PostgreSQL backend.

## Architecture

\`\`\`
Next.js Frontend ──HTTP──> FastAPI Backend ──> PostgreSQL
                                │
                                └──> OpenRouter (DeepSeek free tier)
\`\`\`

See `docs/superpowers/specs/2026-06-25-restaurant-ai-dashboard-design.md` for
the full design spec.

## Setup (Docker Compose — recommended)

1. Copy `backend/.env.example` to `backend/.env` and fill in `JWT_SECRET`
   and `OPENROUTER_API_KEY` (free key from https://openrouter.ai).
2. Run `docker compose up --build`.
3. Backend: http://localhost:8000/health — Frontend: http://localhost:3000

## Setup (manual, for development)

**Backend:**
\`\`\`
cd backend
python -m venv .venv
.venv\\Scripts\\activate   # Windows
pip install -r requirements.txt
copy .env.example .env      # then edit DATABASE_URL to use localhost
uvicorn app.main:app --reload
\`\`\`

**Frontend:**
\`\`\`
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
\`\`\`

## Generating synthetic demo data

\`\`\`
cd backend
python -m scripts.generate_synthetic_data
\`\`\`
Writes one CSV per branch to `backend/scripts/output/`, ready to upload via
the dashboard's upload page.

## Running tests

\`\`\`
cd backend && python -m pytest tests/ -v
cd frontend && npx vitest run
\`\`\`

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | PostgreSQL connection string |
| `JWT_SECRET` | backend | Signs auth tokens |
| `OPENROUTER_API_KEY` | backend | Free-tier DeepSeek access via OpenRouter |
| `OPENROUTER_MODEL` | backend | Defaults to `deepseek/deepseek-chat-v3-0324:free` |
| `FRONTEND_ORIGIN` | backend | CORS allow-list |
| `NEXT_PUBLIC_API_URL` | frontend | Backend base URL |

## Forecast accuracy

`GET /branches/{id}/forecasts/accuracy` returns MAE% and RMSE% computed on a
14-day holdout. Requires at least 28 days of sales history for that branch.

## Known limitations

- Single-tenant: one owner account manages all branches; no multi-company
  support.
- CSV ingestion only — no direct POS API integrations.
- LLM insights are rate-limited to once per hour per branch to respect the
  OpenRouter free-tier quota; a rule-based fallback is used if the LLM call
  fails or returns malformed output.
```

- [ ] **Step 4: Manually verify the full stack via Docker Compose**

Run: `docker compose up --build`
Expected: All three services start; `http://localhost:3000` loads the login page; `http://localhost:8000/health` returns `{"status":"ok"}`.

- [ ] **Step 5: Commit**

```bash
git add frontend/Dockerfile docker-compose.yml README.md
git commit -m "Add frontend Dockerfile, compose integration, and project README"
```

---

## Plan Complete

This concludes the implementation plan across Parts 1-6 (26 tasks total). After
all tasks are executed and committed, the project will have: full backend API
with auth, CSV ingestion, Prophet forecasting with accuracy evaluation,
inventory and staffing intelligence, an LLM insight layer with schema
validation and fallback, a Next.js dashboard consuming all of it, Docker
Compose for one-command local startup, and a README covering setup,
architecture, and limitations — directly addressing the rubric's AI
integration, technical quality, UX, deployment/documentation criteria.

Deployment to a public URL (Vercel/Render/Neon or similar) is a follow-up
decision deferred per the design spec — once this plan is executed and
verified locally, a follow-up plan should cover production deployment.
