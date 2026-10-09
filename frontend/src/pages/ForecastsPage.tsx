import { useState } from "react";
import {
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { TrendingUp, AlertTriangle } from "lucide-react";
import {
  PageHeader,
  Panel,
  KpiCard,
  Badge,
  Select,
  type BadgeTone,
} from "../components/ui";
import { DemoBadge } from "../components/ui";

/* ---------- Selectors ---------- */

const periods = [
  { value: "7d", label: "Next 7 days" },
  { value: "14d", label: "Next 14 days" },
  { value: "28d", label: "Next 28 days" },
] as const;

const products = [
  { value: "milk", label: "Whole Milk 1L" },
  { value: "straw", label: "Strawberries 250g" },
  { value: "spinach", label: "Baby Spinach 200g" },
  { value: "yogurt", label: "Greek Yogurt 500g" },
] as const;

/* ---------- Illustrative forecast data (demo estimates) ---------- */

const forecastSeries: Record<
  (typeof products)[number]["value"],
  { label: string; actual: number | null; predicted: number }[]
> = {
  milk: [
    { label: "Sep 29", actual: 24, predicted: 23 },
    { label: "Sep 30", actual: 26, predicted: 25 },
    { label: "Oct 01", actual: 22, predicted: 24 },
    { label: "Oct 02", actual: 27, predicted: 25 },
    { label: "Oct 03", actual: null, predicted: 26 },
    { label: "Oct 04", actual: null, predicted: 27 },
    { label: "Oct 05", actual: null, predicted: 28 },
  ],
  straw: [
    { label: "Sep 29", actual: 9, predicted: 8 },
    { label: "Sep 30", actual: 10, predicted: 9 },
    { label: "Oct 01", actual: 8, predicted: 9 },
    { label: "Oct 02", actual: 11, predicted: 10 },
    { label: "Oct 03", actual: null, predicted: 11 },
    { label: "Oct 04", actual: null, predicted: 12 },
    { label: "Oct 05", actual: null, predicted: 12 },
  ],
  spinach: [
    { label: "Sep 29", actual: 4, predicted: 4 },
    { label: "Sep 30", actual: 5, predicted: 4 },
    { label: "Oct 01", actual: 5, predicted: 5 },
    { label: "Oct 02", actual: 6, predicted: 5 },
    { label: "Oct 03", actual: null, predicted: 6 },
    { label: "Oct 04", actual: null, predicted: 7 },
    { label: "Oct 05", actual: null, predicted: 7 },
  ],
  yogurt: [
    { label: "Sep 29", actual: 12, predicted: 11 },
    { label: "Sep 30", actual: 13, predicted: 12 },
    { label: "Oct 01", actual: 12, predicted: 12 },
    { label: "Oct 02", actual: 14, predicted: 13 },
    { label: "Oct 03", actual: null, predicted: 14 },
    { label: "Oct 04", actual: null, predicted: 15 },
    { label: "Oct 05", actual: null, predicted: 16 },
  ],
};

const tableRows = [
  {
    product: "Whole Milk 1L",
    recent: "26 / day",
    predicted: "28 / day",
    stock: "20 units",
    risk: "high" as const,
  },
  {
    product: "Strawberries 250g",
    recent: "10 / day",
    predicted: "12 / day",
    stock: "14 packs",
    risk: "medium" as const,
  },
  {
    product: "Baby Spinach 200g",
    recent: "5 / day",
    predicted: "7 / day",
    stock: "3 packs",
    risk: "high" as const,
  },
  {
    product: "Greek Yogurt 500g",
    recent: "13 / day",
    predicted: "16 / day",
    stock: "75 tubs",
    risk: "low" as const,
  },
];

/* ---------- Page ---------- */

export default function ForecastsPage() {
  const [period, setPeriod] = useState<(typeof periods)[number]["value"]>("7d");
  const [product, setProduct] = useState<(typeof products)[number]["value"]>("milk");

  const data = forecastSeries[product];
  const productLabel = products.find((p) => p.value === product)?.label ?? "";
  const periodLabel = periods.find((p) => p.value === period)?.label ?? "";

  const lastActualIdx = data.reduce((acc, d, i) => (d.actual !== null ? i : acc), 0);

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="Demand forecasts"
        subtitle="Compare recent sales history against predicted demand. Predicted values below are illustrative demo estimates, not live model output."
        action={
          <>
            <Select ariaLabel="Forecast period" value={period} onChange={setPeriod} options={periods} />
            <Select ariaLabel="Product" value={product} onChange={setProduct} options={products} />
            <DemoBadge />
          </>
        }
      />

      {/* Summary KPIs */}
      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Avg daily demand"
          value={
            data.length > 0
              ? String(Math.round(data.reduce((s, d) => s + d.predicted, 0) / data.length))
              : "—"
          }
          note="units / day, demo estimate"
          icon={<TrendingUp size={15} />}
        />
        <KpiCard
          label={`${productLabel} stockout window`}
          value={product === "milk" ? "Oct 04" : product === "spinach" ? "Oct 03" : product === "straw" ? "Oct 05" : "—"}
          change={product === "yogurt" ? "Low" : "Elevated"}
          changeTone={product === "yogurt" ? "green" : "amber"}
          note="projected at current velocity"
          icon={<AlertTriangle size={15} />}
        />
        <KpiCard
          label="Forecast period"
          value={periodLabel}
          note="selected horizon"
          icon={<TrendingUp size={15} />}
        />
        <KpiCard
          label="SKUs forecastable"
          value="4"
          note="with sufficient sales history"
          icon={<TrendingUp size={15} />}
        />
      </div>

      {/* Chart */}
      <Panel
        title="Actual vs predicted demand"
        subtitle={`${productLabel} · solid = observed sales, dashed = predicted (demo estimates)`}
        className="mb-5"
      >
        <div className="h-[260px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 20, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e8ece7" />
              <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: "#818b83", fontSize: 11 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "#818b83", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #e6e8e3", fontSize: 11 }}
                labelStyle={{ fontWeight: 700 }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line
                type="monotone"
                dataKey="actual"
                name="Actual sales"
                stroke="#287452"
                strokeWidth={2.5}
                dot={{ r: 3 }}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="predicted"
                name="Predicted (demo estimate)"
                stroke="#816ac1"
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-2 text-center text-[10px] text-[#9aa39b]">
          History ends at {data[lastActualIdx]?.label}; later points are predictions.
        </p>
      </Panel>

      {/* Table */}
      <Panel
        title="Demand risk summary"
        subtitle="Recent sales vs predicted demand across tracked SKUs (demo estimates)"
      >
        <div className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
          <table className="w-full min-w-[560px] text-left">
            <thead>
              <tr className="border-b border-[#eef0ec] text-left text-[10px] font-bold uppercase tracking-wider text-[#9aa39b]">
                <th className="py-2.5 pr-3">Product</th>
                <th className="py-2.5 pr-3 text-right">Recent sales</th>
                <th className="py-2.5 pr-3 text-right">Predicted</th>
                <th className="py-2.5 pr-3 text-right">Available stock</th>
                <th className="py-2.5">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#eff1ed]">
              {tableRows.map((r) => (
                <tr key={r.product} className="text-[11px] text-[#5c6b62] hover:bg-[#fafbfa]">
                  <td className="py-2.5 pr-3 font-semibold text-[#39473d]">{r.product}</td>
                  <td className="py-2.5 pr-3 text-right">{r.recent}</td>
                  <td className="py-2.5 pr-3 text-right">{r.predicted}</td>
                  <td className="py-2.5 pr-3 text-right">{r.stock}</td>
                  <td className="py-2.5">
                    <RiskBadge risk={r.risk} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

function RiskBadge({ risk }: { risk: "high" | "medium" | "low" }) {
  const tone: BadgeTone = risk === "high" ? "red" : risk === "medium" ? "amber" : "green";
  return <Badge tone={tone}>{risk}</Badge>;
}
