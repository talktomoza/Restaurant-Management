"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AnimatedCounter from "@/components/AnimatedCounter";
import {
  Branch,
  ForecastPoint,
  HeatmapCell,
  InsightContent,
  InventoryAlert,
  KpiSummary,
  ShiftRecommendation,
  clearToken,
  createBranch,
  generateForecast,
  generateWeeklyInsight,
  getForecastAccuracy,
  getHeatmap,
  getInventoryAlerts,
  getKpis,
  getStaffing,
  getToken,
  listBranches,
  uploadCsv,
} from "@/lib/api";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Showcase data — illustrative until the live backend features (Tasks 11-16) are wired up
const KPI_SHOWCASE = [
  { label: "Today's Revenue", value: "$4,820", delta: "+12.4%", up: true },
  { label: "Order Count", value: "318", delta: "+5.1%", up: true },
  { label: "Avg Order Value", value: "$15.16", delta: "-1.8%", up: false },
  { label: "Active Branches", value: "3", delta: "stable", up: true },
];

const HEATMAP_HOURS = ["10am", "12pm", "2pm", "4pm", "6pm", "8pm", "10pm"];
const HEATMAP_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HEATMAP_DATA: number[][] = HEATMAP_DAYS.map((_, d) =>
  HEATMAP_HOURS.map((_, h) => {
    const base = Math.sin((h / HEATMAP_HOURS.length) * Math.PI) * 70;
    const weekend = d >= 4 ? 25 : 0;
    return Math.round(20 + base + weekend);
  })
);

const INVENTORY_SHOWCASE = [
  { item: "Chicken Breast", status: "Stockout Risk", daysLeft: 1.5, level: "danger" },
  { item: "Tomato Sauce", status: "Reorder Soon", daysLeft: 4, level: "warning" },
  { item: "Burger Buns", status: "Healthy", daysLeft: 9, level: "ok" },
  { item: "Cheese Slices", status: "Overstock", daysLeft: 21, level: "info" },
];

const STAFFING_SHOWCASE = [
  { shift: "Morning (7-12)", recommended: 4, scheduled: 4 },
  { shift: "Afternoon (12-5)", recommended: 7, scheduled: 5 },
  { shift: "Evening (5-11)", recommended: 9, scheduled: 8 },
];

const INSIGHTS_SHOWCASE = [
  "📈 Friday and Saturday evenings (6-9pm) are projected to see 34% more traffic — schedule extra staff.",
  "📦 Chicken Breast stock will run out in 1.5 days based on predicted demand — reorder today.",
  "💰 Downtown branch revenue is up 12% vs last week, driven mainly by dinner-time orders.",
  "⚠️ Cheese Slices are overstocked — reduce ordering for the next 2 weeks to free up locked capital.",
];

const TOP_SELLERS_SHOWCASE = [
  { rank: 1, item: "Classic Burger", units: 482 },
  { rank: 2, item: "Margherita Pizza", units: 401 },
  { rank: 3, item: "Chicken Wings", units: 356 },
  { rank: 4, item: "Iced Latte", units: 298 },
  { rank: 5, item: "Caesar Salad", units: 211 },
];
const TOP_SELLERS_MAX = Math.max(...TOP_SELLERS_SHOWCASE.map((s) => s.units));

function getBranchStatus(now: Date): { label: string; open: boolean } {
  const hour = now.getHours();
  const open = hour >= 9 && hour < 23;
  return { label: open ? "Open Now" : "Closed", open };
}

function heatColor(value: number) {
  if (value < 40) return "#1e293b";
  if (value < 60) return "#3730a3";
  if (value < 80) return "#6366f1";
  if (value < 100) return "#818cf8";
  return "#c7d2fe";
}

export default function DashboardPage() {
  const router = useRouter();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<number | null>(null);
  const [newBranchName, setNewBranchName] = useState("");
  const [newBranchLocation, setNewBranchLocation] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [accuracy, setAccuracy] = useState<{ mae_pct: number | null; rmse_pct: number | null } | null>(null);
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [now, setNow] = useState<Date | null>(null);
  const [inventoryAlerts, setInventoryAlerts] = useState<InventoryAlert[] | null>(null);
  const [staffing, setStaffing] = useState<ShiftRecommendation[] | null>(null);
  const [insight, setInsight] = useState<InsightContent | null>(null);
  const [insightBusy, setInsightBusy] = useState(false);
  const [kpis, setKpis] = useState<KpiSummary | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapCell[] | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    refreshBranches();
  }, [router]);

  useEffect(() => {
    if (!selectedBranch) return;
    getInventoryAlerts(selectedBranch)
      .then(setInventoryAlerts)
      .catch(() => setInventoryAlerts(null));
    const today = new Date().toISOString().slice(0, 10);
    getStaffing(selectedBranch, today)
      .then(setStaffing)
      .catch(() => setStaffing(null));
    const end = new Date();
    const start = new Date(end);
    start.setDate(start.getDate() - 6);
    const startDate = start.toISOString().slice(0, 10);
    const endDate = end.toISOString().slice(0, 10);
    getKpis(selectedBranch, startDate, endDate)
      .then(setKpis)
      .catch(() => setKpis(null));
    getHeatmap(selectedBranch, startDate, endDate)
      .then(setHeatmap)
      .catch(() => setHeatmap(null));
  }, [selectedBranch]);

  async function handleGenerateInsight() {
    if (!selectedBranch) return;
    setInsightBusy(true);
    try {
      const result = await generateWeeklyInsight(selectedBranch);
      setInsight(result);
    } catch {
      setInsight(null);
    } finally {
      setInsightBusy(false);
    }
  }

  useEffect(() => {
    setNow(new Date());
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  async function refreshBranches() {
    try {
      const data = await listBranches();
      setBranches(data);
      if (data.length > 0 && selectedBranch === null) setSelectedBranch(data[0].id);
    } catch {
      setErrorMsg("Failed to load branches.");
    }
  }

  async function handleCreateBranch(e: React.FormEvent) {
    e.preventDefault();
    if (!newBranchName.trim()) return;
    setBusy(true);
    setErrorMsg(null);
    try {
      const branch = await createBranch(newBranchName, newBranchLocation);
      setNewBranchName("");
      setNewBranchLocation("");
      await refreshBranches();
      setSelectedBranch(branch.id);
    } catch {
      setErrorMsg("Failed to create branch.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!uploadFile || !selectedBranch) return;
    setBusy(true);
    setErrorMsg(null);
    setUploadResult(null);
    try {
      const result = await uploadCsv(selectedBranch, uploadFile, {
        date_column: "Date",
        item_column: "Item",
        quantity_column: "Qty",
        amount_column: "Total",
      });
      setUploadResult(
        `✅ ${result.rows_imported} rows imported, ${result.rows_rejected} rejected.`
      );
    } catch (err) {
      setErrorMsg(`Upload failed: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleForecast() {
    if (!selectedBranch) return;
    setBusy(true);
    setErrorMsg(null);
    try {
      const points = await generateForecast(selectedBranch, 14);
      setForecast(points);
      try {
        const acc = await getForecastAccuracy(selectedBranch);
        setAccuracy(acc);
      } catch {
        setAccuracy(null);
      }
    } catch (err) {
      setErrorMsg(`Failed to generate forecast: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Top bar */}
      <header className="flex items-center justify-between border-b border-white/10 bg-slate-900/60 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🍽️</span>
          <div>
            <h1 className="text-lg font-bold leading-tight text-white">
              Restaurant Analytics
            </h1>
            <p className="text-xs text-slate-400">AI-Powered Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {now && (
            <div className="hidden items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 sm:flex">
              <span
                className={`h-2 w-2 rounded-full ${
                  getBranchStatus(now).open ? "bg-emerald-400 shadow-[0_0_6px_2px_rgba(52,211,153,0.6)]" : "bg-rose-400"
                }`}
              />
              <span className="font-medium">{getBranchStatus(now).label}</span>
              <span className="text-slate-500">·</span>
              <span suppressHydrationWarning>
                {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </span>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-300 transition hover:bg-white/5"
          >
            Log Out
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-6">
        {errorMsg && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-300">
            {errorMsg}
          </div>
        )}

        {/* KPI cards */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {kpis
            ? [
                { label: "7-Day Revenue", value: `$${kpis.total_revenue.toFixed(2)}`, delta: "Live", up: true },
                { label: "Order Count", value: String(kpis.order_count), delta: "Live", up: true },
                { label: "Avg Order Value", value: `$${kpis.average_order_value.toFixed(2)}`, delta: "Live", up: true },
                { label: "Active Branches", value: String(branches.length), delta: "Live", up: true },
              ].map((kpi) => (
                <div
                  key={kpi.label}
                  className="rounded-xl border border-white/10 bg-gradient-to-br from-slate-900 to-slate-800/60 p-4 shadow-lg"
                >
                  <p className="text-xs text-slate-400">{kpi.label}</p>
                  <p className="mt-1 text-2xl font-bold text-white">
                    <AnimatedCounter value={kpi.value} />
                  </p>
                  <p className="mt-1 text-xs font-medium text-emerald-400">{kpi.delta}</p>
                </div>
              ))
            : KPI_SHOWCASE.map((kpi) => (
                <div
                  key={kpi.label}
                  className="rounded-xl border border-white/10 bg-gradient-to-br from-slate-900 to-slate-800/60 p-4 shadow-lg"
                >
                  <p className="text-xs text-slate-400">{kpi.label}</p>
                  <p className="mt-1 text-2xl font-bold text-white">
                    <AnimatedCounter value={kpi.value} />
                  </p>
                  <p className={`mt-1 text-xs font-medium ${kpi.up ? "text-emerald-400" : "text-rose-400"}`}>
                    {kpi.delta}
                  </p>
                </div>
              ))}
        </div>
        <p className="mb-4 -mt-3 text-xs text-slate-500">
          {kpis ? "Live totals — last 7 days" : "* Showcase data — select a branch with sales history to see live totals"}
        </p>

        <div className="space-y-10">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Branches */}
            <section className="rounded-xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
              <h2 className="mb-3 text-lg font-semibold text-white">Branches</h2>
              <ul className="mb-4 space-y-1.5">
                {branches.map((b) => (
                  <li key={b.id}>
                    <button
                      onClick={() => setSelectedBranch(b.id)}
                      className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition ${
                        selectedBranch === b.id
                          ? "bg-indigo-500/20 font-semibold text-indigo-300 ring-1 ring-indigo-400/40"
                          : "text-slate-300 hover:bg-white/5"
                      }`}
                    >
                      <span>
                        {b.name} <span className="text-slate-500">— {b.location}</span>
                      </span>
                      {now && (
                        <span
                          className={`ml-2 shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                            getBranchStatus(now).open
                              ? "bg-emerald-500/15 text-emerald-300"
                              : "bg-rose-500/15 text-rose-300"
                          }`}
                        >
                          {getBranchStatus(now).label}
                        </span>
                      )}
                    </button>
                  </li>
                ))}
                {branches.length === 0 && (
                  <li className="text-sm text-slate-500">No branches yet</li>
                )}
              </ul>
              <form onSubmit={handleCreateBranch} className="space-y-2.5">
                <input
                  className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30"
                  placeholder="Branch name"
                  value={newBranchName}
                  onChange={(e) => setNewBranchName(e.target.value)}
                />
                <input
                  className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30"
                  placeholder="Location"
                  value={newBranchLocation}
                  onChange={(e) => setNewBranchLocation(e.target.value)}
                />
                <button
                  type="submit"
                  disabled={busy}
                  className="w-full rounded-lg bg-indigo-500 px-3.5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-400 disabled:opacity-50"
                >
                  + Add New Branch
                </button>
              </form>
            </section>

            {/* Upload */}
            <section className="rounded-xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
              <h2 className="mb-3 text-lg font-semibold text-white">Upload CSV Data</h2>
              <p className="mb-3 text-xs text-slate-400">Columns: Date, Item, Qty, Total</p>
              <form onSubmit={handleUpload} className="space-y-3">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                  className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-500 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white"
                />
                <button
                  type="submit"
                  disabled={busy || !uploadFile || !selectedBranch}
                  className="w-full rounded-lg bg-emerald-500 px-3.5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition hover:bg-emerald-400 disabled:opacity-50"
                >
                  Upload
                </button>
              </form>
              {uploadResult && (
                <p className="mt-3 rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
                  {uploadResult}
                </p>
              )}
            </section>

            {/* Peak hour heatmap */}
            <section className="rounded-xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
              <h2 className="mb-3 text-lg font-semibold text-white">Peak Hour Heatmap</h2>
              {(() => {
                const grid: number[][] = heatmap && heatmap.length > 0
                  ? HEATMAP_DAYS.map((_, d) =>
                      HEATMAP_HOURS.map((_, h) => {
                        const hour = [10, 12, 14, 16, 18, 20, 22][h];
                        const cell = heatmap.find((c) => c.day_of_week === d && c.hour === hour);
                        return cell ? cell.revenue : 0;
                      })
                    )
                  : HEATMAP_DATA;
                const max = Math.max(1, ...grid.flat());
                return (
                  <div className="space-y-1.5">
                    {HEATMAP_DAYS.map((day, d) => (
                      <div key={day} className="flex items-center gap-1.5">
                        <span className="w-9 text-[11px] text-slate-400">{day}</span>
                        <div className="flex flex-1 gap-1">
                          {HEATMAP_HOURS.map((hour, h) => {
                            const value = heatmap && heatmap.length > 0 ? (grid[d][h] / max) * 100 : grid[d][h];
                            return (
                              <div
                                key={hour}
                                title={`${day} ${hour}: ${heatmap && heatmap.length > 0 ? `$${grid[d][h].toFixed(2)}` : `${grid[d][h]} orders`}`}
                                className="h-5 flex-1 rounded-sm"
                                style={{ backgroundColor: heatColor(value) }}
                              />
                            );
                          })}
                        </div>
                      </div>
                    ))}
                    <div className="flex gap-1.5 pl-9 pt-1">
                      {HEATMAP_HOURS.map((hour) => (
                        <span key={hour} className="flex-1 text-center text-[10px] text-slate-500">
                          {hour}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })()}
              <p className="mt-2 text-[11px] text-slate-500">
                {heatmap && heatmap.length > 0
                  ? "Live revenue by day/hour — last 7 days"
                  : "* Showcase data — live heatmap appears once sales history exists"}
              </p>
            </section>
          </div>

          {/* Top Sellers */}
          <section>
            <h2 className="mb-1 flex items-center gap-2 text-xl font-bold text-white">
              <span>🏆</span> Top-Selling Items
            </h2>
            <p className="mb-4 text-xs text-slate-500">* Showcase data — live aggregation ships in a later task</p>
            <div className="rounded-xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
              <ul className="space-y-3">
                {TOP_SELLERS_SHOWCASE.map((s) => (
                  <li key={s.rank} className="flex items-center gap-3">
                    <span
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        s.rank === 1
                          ? "bg-amber-400/20 text-amber-300"
                          : s.rank === 2
                          ? "bg-slate-400/20 text-slate-300"
                          : s.rank === 3
                          ? "bg-orange-400/20 text-orange-300"
                          : "bg-white/5 text-slate-500"
                      }`}
                    >
                      {s.rank}
                    </span>
                    <span className="w-36 shrink-0 text-sm text-slate-200">{s.item}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-violet-400"
                        style={{ width: `${(s.units / TOP_SELLERS_MAX) * 100}%` }}
                      />
                    </div>
                    <span className="w-14 shrink-0 text-right text-xs text-slate-400">{s.units} sold</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* Forecast */}
          <section>
            <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
              <span>📈</span> Revenue Forecast (Prophet AI)
            </h2>
            <div className="rounded-xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-slate-400">14-day projection generated from uploaded sales history</p>
                <button
                  onClick={handleForecast}
                  disabled={busy || !selectedBranch}
                  className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-amber-500/20 transition hover:bg-amber-400 disabled:opacity-50"
                >
                  Generate 14-Day Forecast
                </button>
              </div>
              {accuracy && (
                <p className="mb-3 text-xs text-slate-400">
                  MAE%: {accuracy.mae_pct?.toFixed(2) ?? "N/A"} · RMSE%: {accuracy.rmse_pct?.toFixed(2) ?? "N/A"}
                </p>
              )}
              {forecast.length > 0 ? (
                <ResponsiveContainer width="100%" height={360}>
                  <LineChart data={forecast}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} />
                    <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                    <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
                    <Legend />
                    <Line type="monotone" dataKey="predicted_revenue" stroke="#818cf8" name="Predicted Revenue" strokeWidth={2.5} dot={false} />
                    <Line type="monotone" dataKey="lower_bound" stroke="#475569" name="Lower Bound" strokeDasharray="4 4" dot={false} />
                    <Line type="monotone" dataKey="upper_bound" stroke="#475569" name="Upper Bound" strokeDasharray="4 4" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="py-12 text-center text-sm text-slate-500">
                  Click the button above to generate a forecast for a branch
                </p>
              )}
            </div>
          </section>

          {/* Inventory */}
          <section>
            <h2 className="mb-1 flex items-center gap-2 text-xl font-bold text-white">
              <span>📦</span> Inventory Intelligence
            </h2>
            <p className="mb-4 text-xs text-slate-500">
              {inventoryAlerts && inventoryAlerts.length > 0
                ? "Live alerts from sales-consumption analysis"
                : "* Showcase data — live alerts appear once a branch has 14+ days of sales history"}
            </p>
            <div className="overflow-hidden rounded-xl border border-white/10 bg-slate-900/60 shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-white/5 text-left text-slate-400">
                  <tr>
                    <th className="px-4 py-2.5">Item</th>
                    <th className="px-4 py-2.5">Status</th>
                    <th className="px-4 py-2.5">Days Left</th>
                  </tr>
                </thead>
                <tbody>
                  {inventoryAlerts && inventoryAlerts.length > 0
                    ? inventoryAlerts.map((row) => (
                        <tr key={row.sku} className="border-t border-white/5">
                          <td className="px-4 py-2.5 text-slate-200">{row.name}</td>
                          <td className="px-4 py-2.5">
                            <span
                              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                                row.alert_type === "stockout_risk"
                                  ? "bg-rose-500/15 text-rose-300"
                                  : "bg-sky-500/15 text-sky-300"
                              }`}
                            >
                              {row.alert_type === "stockout_risk" ? "Stockout Risk" : "Overstock"}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-slate-300">{row.days_to_run_out ?? "—"}</td>
                        </tr>
                      ))
                    : INVENTORY_SHOWCASE.map((row) => (
                        <tr key={row.item} className="border-t border-white/5">
                          <td className="px-4 py-2.5 text-slate-200">{row.item}</td>
                          <td className="px-4 py-2.5">
                            <span
                              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                                row.level === "danger"
                                  ? "bg-rose-500/15 text-rose-300"
                                  : row.level === "warning"
                                  ? "bg-amber-500/15 text-amber-300"
                                  : row.level === "info"
                                  ? "bg-sky-500/15 text-sky-300"
                                  : "bg-emerald-500/15 text-emerald-300"
                              }`}
                            >
                              {row.status}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-slate-300">{row.daysLeft}</td>
                        </tr>
                      ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Staffing */}
          <section>
            <h2 className="mb-1 flex items-center gap-2 text-xl font-bold text-white">
              <span>👥</span> Shift Planner
            </h2>
            <p className="mb-4 text-xs text-slate-500">
              {staffing && staffing.length > 0
                ? "Live recommendation from today's order volume"
                : "* Showcase data — live recommendation appears once sales data exists for today"}
            </p>
            <div className="rounded-xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  data={
                    staffing && staffing.length > 0
                      ? staffing.map((s) => ({ shift: s.shift, recommended: s.recommended_staff_count }))
                      : STAFFING_SHOWCASE
                  }
                >
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                  <XAxis dataKey="shift" tick={{ fontSize: 11, fill: "#94a3b8" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                  <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
                  <Legend />
                  <Bar dataKey="recommended" name="Recommended" radius={[6, 6, 0, 0]}>
                    {(staffing && staffing.length > 0 ? staffing : STAFFING_SHOWCASE).map((_, i) => (
                      <Cell key={i} fill="#818cf8" />
                    ))}
                  </Bar>
                  {!(staffing && staffing.length > 0) && (
                    <Bar dataKey="scheduled" name="Scheduled" radius={[6, 6, 0, 0]}>
                      {STAFFING_SHOWCASE.map((_, i) => (
                        <Cell key={i} fill="#475569" />
                      ))}
                    </Bar>
                  )}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Insights */}
          <section>
            <div className="mb-1 flex flex-wrap items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 text-xl font-bold text-white">
                <span>✨</span> AI-Generated Insights
              </h2>
              <button
                onClick={handleGenerateInsight}
                disabled={insightBusy || !selectedBranch}
                className="rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 transition hover:bg-violet-400 disabled:opacity-50"
              >
                {insightBusy ? "Generating..." : "Generate Weekly Summary (DeepSeek AI)"}
              </button>
            </div>
            <p className="mb-4 text-xs text-slate-500">
              {insight
                ? "Live result from DeepSeek (via OpenRouter), with rule-based fallback if the LLM is unavailable"
                : "* Showcase data — click the button above to generate a live AI summary for the selected branch"}
            </p>
            <div className="rounded-xl border border-white/10 bg-slate-900/60 p-5 shadow-sm">
              {insight ? (
                <div className="space-y-3">
                  <div className="rounded-lg border border-indigo-400/20 bg-indigo-500/5 px-4 py-3 text-sm text-slate-200">
                    {insight.summary}
                  </div>
                  {insight.key_risks.map((risk, i) => (
                    <div
                      key={`risk-${i}`}
                      className="rounded-lg border border-rose-400/20 bg-rose-500/5 px-4 py-3 text-sm text-slate-200"
                    >
                      ⚠️ {risk}
                    </div>
                  ))}
                  {insight.recommendations.map((rec, i) => (
                    <div
                      key={`rec-${i}`}
                      className="rounded-lg border border-emerald-400/20 bg-emerald-500/5 px-4 py-3 text-sm text-slate-200"
                    >
                      ✅ {rec}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {INSIGHTS_SHOWCASE.map((text, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-indigo-400/20 bg-indigo-500/5 px-4 py-3 text-sm text-slate-200"
                    >
                      {text}
                    </div>
                  ))}
                </div>
              )}
              <ResponsiveContainer width="100%" height={180} className="mt-5">
                <AreaChart data={STAFFING_SHOWCASE.map((s, i) => ({ name: s.shift, value: 40 + i * 25 }))}>
                  <defs>
                    <linearGradient id="insightFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#818cf8" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#818cf8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#94a3b8" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                  <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
                  <Area type="monotone" dataKey="value" stroke="#818cf8" fill="url(#insightFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
