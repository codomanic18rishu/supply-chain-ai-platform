/**
 * MultiProductDashboard.tsx
 * Enterprise-grade multi-product forecast dashboard.
 * Drop into: frontend/src/pages/MultiProductDashboard.tsx
 *
 * Dependencies (should already be in your Vite project):
 *   axios, recharts, lucide-react, tailwindcss
 *
 * Assumes: frontend/src/api.ts exports a default Axios instance as `api`.
 */

import React, { useState, useCallback, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,

  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  Upload,
  AlertTriangle,
  TrendingUp,
  Package,
  Brain,
  FileText,
  ChevronUp,
  ChevronDown,
  Minus,
  RefreshCw,
  ShieldAlert,
  BarChart3,
  Boxes,
  Cpu,
  CloudUpload,
  X,
} from "lucide-react";
import api from "../services/api";

// ─────────────────────────────────────────────
// TypeScript Interfaces — matches backend schema
// ─────────────────────────────────────────────

export interface ForecastDataPoint {
  date: string;
  historical?: number | null;
  forecast?: number | null;
  lower_bound?: number | null;
  upper_bound?: number | null;
}

export interface TopProduct {
  rank: number;
  product_id: string;
  product_name: string;
  total_forecast: number;
  growth_rate: number; // percentage, e.g. 12.5
  confidence_score: number; // 0–1
  category?: string;
}

export interface InventoryOptimization {
  product_id: string;
  product_name: string;
  safety_stock: number;
  reorder_point: number;
  reorder_quantity: number;
  current_stock?: number;
  stock_unit?: string;
  lead_time_days?: number;
}

export type RiskSeverity = "critical" | "high" | "medium" | "low" | "info";

export interface RiskAlert {
  alert_id: string;
  product_id: string;
  product_name: string;
  severity: RiskSeverity;
  category: string;
  message: string;
  recommended_action?: string;
  triggered_at?: string;
}

export interface AIInsight {
  title: string;
  body: string;
  tags?: string[];
}

export interface DashboardMetadata {
  report_generated_at: string;
  forecast_horizon_days: number;
  total_products_analyzed: number;
  total_sku_count?: number;
  model_version?: string;
  data_freshness?: string;
  currency?: string;
}

export interface MultiProductForecastResponse {
  metadata: DashboardMetadata;
  top_products: TopProduct[];
  forecast_chart_data: Record<string, ForecastDataPoint[]>; // keyed by product_id
  inventory_optimizations: InventoryOptimization[];
  risk_alerts: RiskAlert[];
  ai_insights: AIInsight[];
  executive_summary?: string;
}

// ─────────────────────────────────────────────
// Constants & Helpers
// ─────────────────────────────────────────────

const SEVERITY_CONFIG: Record<
  RiskSeverity,
  { label: string; bg: string; text: string; border: string; icon: string }
> = {
  critical: {
    label: "Critical",
    bg: "bg-red-950/60",
    text: "text-red-300",
    border: "border-red-700/60",
    icon: "🔴",
  },
  high: {
    label: "High",
    bg: "bg-orange-950/60",
    text: "text-orange-300",
    border: "border-orange-700/60",
    icon: "🟠",
  },
  medium: {
    label: "Medium",
    bg: "bg-yellow-950/60",
    text: "text-yellow-300",
    border: "border-yellow-700/60",
    icon: "🟡",
  },
  low: {
    label: "Low",
    bg: "bg-blue-950/60",
    text: "text-blue-300",
    border: "border-blue-700/60",
    icon: "🔵",
  },
  info: {
    label: "Info",
    bg: "bg-slate-800/60",
    text: "text-slate-300",
    border: "border-slate-600/60",
    icon: "⚪",
  },
};

const CHART_COLORS = [
  "#38bdf8", // sky-400
  "#a78bfa", // violet-400
  "#34d399", // emerald-400
  "#fb923c", // orange-400
  "#f472b6", // pink-400
  "#facc15", // yellow-400
];

function fmt(n: number, decimals = 0): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(decimals);
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function confidenceColor(score: number): string {
  if (score >= 0.85) return "text-emerald-400";
  if (score >= 0.65) return "text-yellow-400";
  return "text-red-400";
}

// ─────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────

// ── Upload Zone ──────────────────────────────

interface UploadZoneProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
  error: string | null;
  onClearError: () => void;
}

const UploadZone: React.FC<UploadZoneProps> = ({
  onUpload,
  isLoading,
  error,
  onClearError,
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file && file.name.endsWith(".csv")) {
        setSelectedFile(file);
      }
    },
    []
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleSubmit = () => {
    if (selectedFile) onUpload(selectedFile);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      {/* Header */}
      <div className="mb-10 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-semibold tracking-widest uppercase mb-4">
          <Cpu size={12} />
          AI-Powered Forecasting Engine
        </div>
        <h1 className="text-4xl font-bold text-white tracking-tight mb-2">
          Multi-Product Forecast
          <span className="text-sky-400"> Dashboard</span>
        </h1>
        <p className="text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
          Upload your product CSV to generate demand forecasts, inventory
          optimizations, and executive AI insights.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        className={`
          relative w-full max-w-lg rounded-2xl border-2 border-dashed transition-all duration-200 cursor-pointer
          ${dragOver
            ? "border-sky-400 bg-sky-500/10 scale-[1.02]"
            : "border-slate-600 bg-slate-800/40 hover:border-slate-500 hover:bg-slate-800/60"
          }
        `}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileChange}
        />
        <div className="flex flex-col items-center justify-center py-14 px-6 text-center">
          <div
            className={`
              p-4 rounded-2xl mb-4 transition-colors
              ${dragOver ? "bg-sky-500/20" : "bg-slate-700/60"}
            `}
          >
            <CloudUpload
              size={32}
              className={dragOver ? "text-sky-400" : "text-slate-400"}
            />
          </div>
          {selectedFile ? (
            <>
              <p className="text-white font-semibold text-sm mb-1">
                {selectedFile.name}
              </p>
              <p className="text-slate-500 text-xs">
                {(selectedFile.size / 1024).toFixed(1)} KB · Click to change
              </p>
            </>
          ) : (
            <>
              <p className="text-slate-300 font-medium text-sm mb-1">
                Drop your CSV here
              </p>
              <p className="text-slate-500 text-xs">
                or click to browse files
              </p>
            </>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 w-full max-w-lg flex items-start gap-3 px-4 py-3 rounded-xl bg-red-950/50 border border-red-700/50 text-red-300 text-sm">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={onClearError}>
            <X size={14} className="text-red-400 hover:text-red-200" />
          </button>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!selectedFile || isLoading}
        className={`
          mt-6 flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-sm transition-all duration-200
          ${selectedFile && !isLoading
            ? "bg-sky-500 hover:bg-sky-400 text-white shadow-lg shadow-sky-500/25 hover:shadow-sky-500/40 hover:-translate-y-0.5"
            : "bg-slate-700 text-slate-500 cursor-not-allowed"
          }
        `}
      >
        {isLoading ? (
          <>
            <RefreshCw size={16} className="animate-spin" />
            Analyzing…
          </>
        ) : (
          <>
            <Upload size={16} />
            Generate Forecast
          </>
        )}
      </button>
    </div>
  );
};

// ── Loading Spinner ───────────────────────────

const LoadingOverlay: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
    <div className="relative">
      <div className="w-16 h-16 rounded-full border-4 border-slate-700" />
      <div className="absolute inset-0 w-16 h-16 rounded-full border-4 border-transparent border-t-sky-400 animate-spin" />
    </div>
    <div className="text-center">
      <p className="text-white font-semibold mb-1">Processing your data</p>
      <p className="text-slate-500 text-sm">
        Running AI forecast models — this may take a moment…
      </p>
    </div>
    <div className="flex gap-1.5 mt-2">
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="w-1.5 h-6 rounded-full bg-sky-500 animate-pulse"
          style={{ animationDelay: `${i * 120}ms` }}
        />
      ))}
    </div>
  </div>
);

// ── Stat Card ────────────────────────────────

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  icon,
  label,
  value,
  sub,
  accent = "text-sky-400",
}) => (
  <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 flex items-start gap-4">
    <div className="p-2.5 rounded-xl bg-slate-700/60 text-slate-300 shrink-0">
      {icon}
    </div>
    <div className="min-w-0">
      <p className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-0.5 truncate">
        {label}
      </p>
      <p className={`text-xl font-bold ${accent} leading-tight`}>{value}</p>
      {sub && <p className="text-slate-500 text-xs mt-0.5 truncate">{sub}</p>}
    </div>
  </div>
);

// ── Top Products ──────────────────────────────

interface TopProductsProps {
  products: TopProduct[];
  currency: string;
}

const TopProductsSection: React.FC<TopProductsProps> = ({
  products,
  currency,
}) => (
  <section>
    <SectionHeader
      icon={<TrendingUp size={16} />}
      title="Top Products"
      subtitle="Ranked by forecast volume"
    />
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
      {products.map((p, idx) => {
        const color = CHART_COLORS[idx % CHART_COLORS.length];
        const growthPositive = p.growth_rate >= 0;
        return (
          <div
            key={p.product_id}
            className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 relative overflow-hidden group hover:border-slate-600 transition-colors"
          >
            {/* Rank badge */}
            <div
              className="absolute top-0 right-0 w-12 h-12 flex items-end justify-start pb-1 pl-1 rounded-bl-2xl font-black text-sm opacity-20"
              style={{ backgroundColor: color + "40", color }}
            >
              #{p.rank}
            </div>

            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className="text-white font-semibold text-sm truncate">
                {p.product_name}
              </span>
            </div>

            <p className="text-slate-500 text-xs mb-3 font-mono">
              {p.product_id}
              {p.category ? ` · ${p.category}` : ""}
            </p>

            <div className="flex items-end justify-between">
              <div>
                <p className="text-slate-400 text-xs mb-0.5">Total Forecast</p>
                <p className="text-white text-xl font-bold">
                  {currency}
                  {fmt(p.total_forecast)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-slate-400 text-xs mb-0.5">Growth</p>
                <p
                  className={`text-sm font-semibold flex items-center gap-0.5 justify-end ${
                    growthPositive ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {growthPositive ? (
                    <ChevronUp size={14} />
                  ) : (
                    <ChevronDown size={14} />
                  )}
                  {Math.abs(p.growth_rate).toFixed(1)}%
                </p>
              </div>
            </div>

            {/* Confidence bar */}
            <div className="mt-4">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-500">Confidence</span>
                <span className={confidenceColor(p.confidence_score)}>
                  {(p.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${p.confidence_score * 100}%`,
                    backgroundColor: color,
                  }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  </section>
);

// ── Forecast Chart ────────────────────────────

interface ForecastChartProps {
  data: Record<string, ForecastDataPoint[]>;
  products: TopProduct[];
}

const ForecastChartSection: React.FC<ForecastChartProps> = ({
  data,
  products,
}) => {
  const [selectedProduct, setSelectedProduct] = useState<string>(
    Object.keys(data)[0] ?? ""
  );

  const chartData = data[selectedProduct] ?? [];
  const product = products.find((p) => p.product_id === selectedProduct);

  // Find the boundary between historical and forecast
  const firstForecastIdx = chartData.findIndex(
    (d) => d.historical == null && d.forecast != null
  );
  const splitDate =
    firstForecastIdx > 0 ? chartData[firstForecastIdx].date : null;

  // Flatten to recharts-friendly format
  const merged = chartData.map((d) => ({
    date: fmtDate(d.date),
    rawDate: d.date,
    historical: d.historical ?? undefined,
    forecast: d.forecast ?? undefined,
    lower: d.lower_bound ?? undefined,
    upper: d.upper_bound ?? undefined,
  }));

  return (
    <section>
      <SectionHeader
        icon={<BarChart3 size={16} />}
        title="Historical vs Forecast"
        subtitle="Demand trend with confidence interval"
      />

      {/* Product selector */}
      <div className="flex flex-wrap gap-2 mb-6">
        {Object.keys(data).map((pid, idx) => {
          const prod = products.find((p) => p.product_id === pid);
          const color = CHART_COLORS[idx % CHART_COLORS.length];
          const active = pid === selectedProduct;
          return (
            <button
              key={pid}
              onClick={() => setSelectedProduct(pid)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                ${
                  active
                    ? "text-white border"
                    : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
                }
              `}
              style={
                active
                  ? {
                      backgroundColor: color + "22",
                      borderColor: color + "66",
                      color,
                    }
                  : {}
              }
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: color }}
              />
              {prod?.product_name ?? pid}
            </button>
          );
        })}
      </div>

      <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="text-white font-semibold text-sm">
              {product?.product_name ?? selectedProduct}
            </p>
            <p className="text-slate-500 text-xs">
              {product?.category ?? "Demand forecast"}
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-4 h-0.5 rounded bg-sky-400 inline-block" />
              Historical
            </span>
            <span className="flex items-center gap-1.5">
              <span
                className="w-4 h-0.5 rounded inline-block"
                style={{
                  background:
                    "repeating-linear-gradient(90deg,#a78bfa 0,#a78bfa 4px,transparent 4px,transparent 8px)",
                }}
              />
              Forecast
            </span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={merged}
            margin={{ top: 8, right: 20, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#334155"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => fmt(v)}
              width={48}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "12px",
                color: "#f1f5f9",
                fontSize: 12,
              }}
              labelStyle={{ color: "#94a3b8", marginBottom: 4 }}
              formatter={(value: any) => [fmt(Number(value || 0), 1), ""]}
            />
            {splitDate && (
              <ReferenceLine
                x={fmtDate(splitDate)}
                stroke="#475569"
                strokeDasharray="4 4"
                label={{
                  value: "Forecast start",
                  position: "top",
                  fill: "#64748b",
                  fontSize: 10,
                }}
              />
            )}
            <Line
              type="monotone"
              dataKey="historical"
              stroke="#38bdf8"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: "#38bdf8" }}
              connectNulls
              name="Historical"
            />
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#a78bfa"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
              activeDot={{ r: 4, fill: "#a78bfa" }}
              connectNulls
              name="Forecast"
            />
            <Line
              type="monotone"
              dataKey="upper"
              stroke="#a78bfa"
              strokeWidth={0.75}
              strokeOpacity={0.4}
              dot={false}
              connectNulls
              name="Upper Bound"
            />
            <Line
              type="monotone"
              dataKey="lower"
              stroke="#a78bfa"
              strokeWidth={0.75}
              strokeOpacity={0.4}
              dot={false}
              connectNulls
              name="Lower Bound"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

// ── Inventory Optimization ────────────────────

interface InventoryProps {
  items: InventoryOptimization[];
}

const InventorySection: React.FC<InventoryProps> = ({ items }) => (
  <section>
    <SectionHeader
      icon={<Boxes size={16} />}
      title="Inventory Optimization"
      subtitle="Safety stock, reorder points & quantities"
    />
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {items.map((item, idx) => {
        const color = CHART_COLORS[idx % CHART_COLORS.length];
        const unit = item.stock_unit ?? "units";
        const stockPct = item.current_stock
          ? Math.min((item.current_stock / item.reorder_point) * 100, 150)
          : null;
        const isLow =
          item.current_stock != null &&
          item.current_stock <= item.reorder_point;

        return (
          <div
            key={item.product_id}
            className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-white font-semibold text-sm">
                  {item.product_name}
                </p>
                <p className="text-slate-500 text-xs font-mono mt-0.5">
                  {item.product_id}
                </p>
              </div>
              {item.lead_time_days != null && (
                <span className="text-xs bg-slate-700/60 text-slate-400 px-2 py-0.5 rounded-lg whitespace-nowrap">
                  {item.lead_time_days}d lead
                </span>
              )}
            </div>

            <div className="grid grid-cols-3 gap-3 mb-4">
              {[
                {
                  label: "Safety Stock",
                  value: item.safety_stock,
                  color: "#34d399",
                },
                {
                  label: "Reorder Point",
                  value: item.reorder_point,
                  color: "#facc15",
                },
                {
                  label: "Reorder Qty",
                  value: item.reorder_quantity,
                  color,
                },
              ].map((m) => (
                <div
                  key={m.label}
                  className="bg-slate-900/50 rounded-xl p-3 text-center"
                >
                  <p
                    className="text-base font-bold leading-tight"
                    style={{ color: m.color }}
                  >
                    {fmt(m.value)}
                  </p>
                  <p className="text-slate-500 text-[10px] mt-0.5 leading-tight">
                    {m.label}
                  </p>
                </div>
              ))}
            </div>

            {stockPct != null && (
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500">Current Stock</span>
                  <span className={isLow ? "text-red-400" : "text-slate-400"}>
                    {fmt(item.current_stock!)} {unit}
                    {isLow ? " ⚠ Low" : ""}
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      isLow ? "bg-red-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(stockPct, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  </section>
);

// ── Risk Alerts ───────────────────────────────

interface RiskAlertsProps {
  alerts: RiskAlert[];
}

const RiskAlertsSection: React.FC<RiskAlertsProps> = ({ alerts }) => {
  const [filter, setFilter] = useState<RiskSeverity | "all">("all");

  const severities: Array<RiskSeverity | "all"> = [
    "all",
    "critical",
    "high",
    "medium",
    "low",
    "info",
  ];
  const filtered =
    filter === "all" ? alerts : alerts.filter((a) => a.severity === filter);

  const counts = alerts.reduce(
    (acc, a) => ({ ...acc, [a.severity]: (acc[a.severity] ?? 0) + 1 }),
    {} as Record<string, number>
  );

  return (
    <section>
      <SectionHeader
        icon={<ShieldAlert size={16} />}
        title="Risk Alerts"
        subtitle={`${alerts.length} active alert${alerts.length !== 1 ? "s" : ""} across all products`}
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {severities.map((s) => {
          const cfg = s !== "all" ? SEVERITY_CONFIG[s] : null;
          const active = filter === s;
          return (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize
                ${
                  active
                    ? s === "all"
                      ? "bg-slate-600 text-white"
                      : `${cfg!.bg} ${cfg!.text} border ${cfg!.border}`
                    : "bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600"
                }
              `}
            >
              {s === "all" ? "All" : cfg!.label}
              {s !== "all" && counts[s] ? (
                <span className="ml-1.5 opacity-70">{counts[s]}</span>
              ) : s === "all" ? (
                <span className="ml-1.5 opacity-70">{alerts.length}</span>
              ) : null}
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/50">
                {["Severity", "Product", "Category", "Alert", "Action"].map(
                  (h) => (
                    <th
                      key={h}
                      className="text-left px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="text-center py-10 text-slate-500 text-sm"
                  >
                    No alerts for this severity level.
                  </td>
                </tr>
              ) : (
                filtered.map((alert) => {
                  const cfg = SEVERITY_CONFIG[alert.severity];
                  return (
                    <tr
                      key={alert.alert_id}
                      className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                    >
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border}`}
                        >
                          {cfg.icon} {cfg.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <p className="text-white text-xs font-medium">
                          {alert.product_name}
                        </p>
                        <p className="text-slate-500 text-[11px] font-mono">
                          {alert.product_id}
                        </p>
                      </td>
                      <td className="px-5 py-4 text-slate-400 text-xs whitespace-nowrap">
                        {alert.category}
                      </td>
                      <td className="px-5 py-4 text-slate-300 text-xs max-w-xs">
                        {alert.message}
                      </td>
                      <td className="px-5 py-4 text-slate-400 text-xs max-w-xs">
                        {alert.recommended_action ?? (
                          <Minus size={12} className="text-slate-600" />
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};

// ── AI Insights ───────────────────────────────

interface InsightsProps {
  insights: AIInsight[];
  executiveSummary?: string;
}

const InsightsSection: React.FC<InsightsProps> = ({
  insights,
  executiveSummary,
}) => (
  <section>
    <SectionHeader
      icon={<Brain size={16} />}
      title="AI Executive Insights"
      subtitle="Model-generated strategic analysis"
    />

    {executiveSummary && (
      <div className="bg-linear-to-br from-sky-950/60 to-violet-950/40 border border-sky-700/30 rounded-2xl p-6 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <Brain size={14} className="text-sky-400" />
          <span className="text-sky-400 text-xs font-semibold uppercase tracking-wider">
            Executive Summary
          </span>
        </div>
        <p className="text-slate-200 text-sm leading-relaxed">
          {executiveSummary}
        </p>
      </div>
    )}

    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {insights.map((insight, idx) => (
        <div
          key={idx}
          className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 hover:border-slate-600 transition-colors"
        >
          <div className="flex items-start gap-3 mb-3">
            <div className="p-1.5 rounded-lg bg-violet-500/10 text-violet-400 shrink-0">
              <Brain size={13} />
            </div>
            <p className="text-white text-sm font-semibold leading-snug">
              {insight.title}
            </p>
          </div>
          <p className="text-slate-400 text-xs leading-relaxed">{insight.body}</p>
          {insight.tags && insight.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {insight.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded-md bg-slate-700/60 text-slate-400 text-[10px] font-medium"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  </section>
);

// ── Section Header ────────────────────────────

interface SectionHeaderProps {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({
  icon,
  title,
  subtitle,
}) => (
  <div className="flex items-center gap-3 mb-5">
    <div className="p-2 rounded-xl bg-slate-700/60 text-slate-300">{icon}</div>
    <div>
      <h2 className="text-white font-bold text-base leading-tight">{title}</h2>
      {subtitle && (
        <p className="text-slate-500 text-xs mt-0.5">{subtitle}</p>
      )}
    </div>
  </div>
);

// ─────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────

const MultiProductDashboard: React.FC = () => {
  const [data, setData] = useState<MultiProductForecastResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    setData(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await api.post<MultiProductForecastResponse>(
        "/api/upload-multi-product-forecast/",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setData(response.data);
    } catch (err: unknown) {
      let message = "Upload failed. Please check your file and try again.";
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail
      ) {
        message = (
          err as { response: { data: { detail: string } } }
        ).response.data.detail;
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setData(null);
    setError(null);
  };

  const currency = data?.metadata?.currency ?? "";

  return (
    <div className="min-h-screen bg-slate-900 text-white font-sans">
      {/* Top Nav Bar */}
      <header className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
              <BarChart3 size={18} />
            </div>
            <span className="font-bold text-sm tracking-tight">
              Forecast<span className="text-sky-400">OS</span>
            </span>
            {data && (
              <span className="hidden sm:block text-slate-600 text-xs">
                /
              </span>
            )}
            {data && (
              <span className="hidden sm:block text-slate-400 text-xs">
                Multi-Product Dashboard
              </span>
            )}
          </div>
          {data && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-3 py-1.5 rounded-lg transition-colors"
            >
              <Upload size={12} />
              New Upload
            </button>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload / Loading / Dashboard */}
        {!data && !isLoading && (
          <UploadZone
            onUpload={handleUpload}
            isLoading={isLoading}
            error={error}
            onClearError={() => setError(null)}
          />
        )}

        {isLoading && <LoadingOverlay />}

        {data && (
          <div className="space-y-10 animate-in fade-in duration-500">
            {/* ── Metadata Summary ── */}
            <section>
              <SectionHeader
                icon={<FileText size={16} />}
                title="Report Summary"
                subtitle={`Generated ${new Date(
                  data.metadata.report_generated_at
                ).toLocaleString()}`}
              />
              <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-4">
                <StatCard
                  icon={<Package size={16} />}
                  label="Products Analyzed"
                  value={String(data.metadata.total_products_analyzed)}
                  accent="text-sky-400"
                />
                <StatCard
                  icon={<Boxes size={16} />}
                  label="Total SKUs"
                  value={String(data.metadata.total_sku_count ?? "—")}
                  accent="text-violet-400"
                />
                <StatCard
                  icon={<TrendingUp size={16} />}
                  label="Forecast Horizon"
                  value={`${data.metadata.forecast_horizon_days}d`}
                  accent="text-emerald-400"
                />
                <StatCard
                  icon={<Cpu size={16} />}
                  label="Model Version"
                  value={data.metadata.model_version ?? "—"}
                  accent="text-yellow-400"
                />
                <StatCard
                  icon={<RefreshCw size={16} />}
                  label="Data Freshness"
                  value={data.metadata.data_freshness ?? "—"}
                  accent="text-orange-400"
                />
              </div>
            </section>

            {/* ── Top Products ── */}
            {data.top_products?.length > 0 && (
              <TopProductsSection
                products={data.top_products}
                currency={currency}
              />
            )}

            {/* ── Forecast Chart ── */}
            {data.forecast_chart_data &&
              Object.keys(data.forecast_chart_data).length > 0 && (
                <ForecastChartSection
                  data={data.forecast_chart_data}
                  products={data.top_products}
                />
              )}

            {/* ── Inventory Optimization ── */}
            {data.inventory_optimizations?.length > 0 && (
              <InventorySection items={data.inventory_optimizations} />
            )}

            {/* ── Risk Alerts ── */}
            {data.risk_alerts?.length > 0 && (
              <RiskAlertsSection alerts={data.risk_alerts} />
            )}

            {/* ── AI Insights ── */}
            {(data.ai_insights?.length > 0 || data.executive_summary) && (
              <InsightsSection
                insights={data.ai_insights ?? []}
                executiveSummary={data.executive_summary}
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default MultiProductDashboard;

