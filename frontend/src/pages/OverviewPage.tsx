import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  Boxes,
  TrendingDown,
  ArrowDownUp,
  IndianRupee,
} from "lucide-react";
import {
  PageHeader,
  Panel,
  KpiCard,
  Badge,
  GhostButton,
  PrimaryButton,
  Select,
  EmptyState,
  type BadgeTone,
} from "../components/ui";
import { DemoBadge } from "../components/ui";
import { type RouteId } from "../components/routes";

/* ---------- Date range selector (local state only) ---------- */

const ranges = [
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last quarter" },
] as const;

/* ---------- Illustrative data ---------- */

const chartData = [
  { day: "Mon", sold: 112, waste: 14 },
  { day: "Tue", sold: 126, waste: 11 },
  { day: "Wed", sold: 118, waste: 12 },
  { day: "Thu", sold: 142, waste: 9 },
  { day: "Fri", sold: 154, waste: 8 },
  { day: "Sat", sold: 171, waste: 7 },
  { day: "Sun", sold: 149, waste: 6 },
];

const freshness = [
  {
    emoji: "🥛",
    name: "Whole milk · 1L",
    store: "Store Central · Batch M-104",
    qty: "20 units",
    expiry: "Expires tomorrow",
    risk: "high" as const,
  },
  {
    emoji: "🍓",
    name: "Strawberries · 250g",
    store: "Store North · Batch S-221",
    qty: "14 units",
    expiry: "Expires in 2 days",
    risk: "high" as const,
  },
  {
    emoji: "🥣",
    name: "Greek yogurt · 500g",
    store: "Store Central · Batch Y-089",
    qty: "32 units",
    expiry: "Expires in 3 days",
    risk: "medium" as const,
  },
];

const activity = [
  { time: "09:12", text: "Markdown approved for whole milk batch M-104 by store manager" },
  { time: "08:40", text: "Transfer proposal generated for leafy greens: Store North → Store South" },
  { time: "Yesterday", text: "Freshness scan completed for 8 SKUs across 3 stores" },
  { time: "Yesterday", text: "Donation route matched for expired bread batch B-881 to community kitchen" },
];

/* ---------- Page ---------- */

export default function OverviewPage({
  onNavigate,
}: {
  onNavigate: (id: RouteId) => void;
}) {
  const [range, setRange] = useState<(typeof ranges)[number]["value"]>("7d");
  const rangeLabel = ranges.find((r) => r.value === range)?.label ?? "";

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="Good morning, Jordan"
        subtitle="Your store network is moving 149 units of fresh stock per day. Freshness risk is concentrated in 3 batch groups over the next 48 hours; review the recommendations panel before today's close."
        action={
          <>
            <Select
              ariaLabel="Date range"
              value={range}
              onChange={setRange}
              options={ranges}
            />
            <DemoBadge />
          </>
        }
      />

      {/* Alert banner */}
      <div className="mb-5 flex flex-wrap items-start gap-3 rounded-xl border border-[#f3e5cd] bg-[#fff8ed] px-4 py-3.5">
        <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[#f9e7c9] font-black text-[#b17a30]">
          !
        </span>
        <div className="min-w-0 flex-1">
          <strong className="block text-[12px] font-bold text-[#654e2e]">
            Action needed: 4 recommendations await review
          </strong>
          <p className="mt-0.5 text-[11px] text-[#9b8059]">
            3 batches are approaching expiry within 48 hours. Review suggested actions
            before today's close.
          </p>
        </div>
        <PrimaryButton onClick={() => onNavigate("recommendations")}>
          Review now →
        </PrimaryButton>
      </div>

      {/* KPI cards */}
      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Inventory at risk"
          value="₹24,680"
          change="12.4%"
          changeTone="red"
          note="vs. previous week"
          icon={<Boxes size={15} />}
          explanation="Total stock value whose freshness is trending toward expiry within the selected range. Simulated demo values."
        />
        <KpiCard
          label="Waste rate"
          value="4.8%"
          change="↓ 1.2 pts"
          note="vs. previous week"
          icon={<TrendingDown size={15} />}
          explanation="Proportion of delivered stock discarded before sale. Lower is better."
        />
        <KpiCard
          label="Stockout risk"
          value="7 SKUs"
          change="2 new"
          changeTone="amber"
          note="need attention"
          icon={<ArrowDownUp size={15} />}
          explanation="Products whose predicted demand may exceed available inventory in the next 7 days."
        />
        <KpiCard
          label="Potential savings"
          value="₹18,420"
          change="Estimated"
          changeTone="neutral"
          note="open proposals"
          icon={<IndianRupee size={15} />}
          explanation="Modelled savings if all open recommendations are approved. Illustrative only."
        />
      </div>

      {/* Charts + freshness */}
      <div className="mb-5 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel
          title="Sales & waste trend"
          subtitle={`${rangeLabel} · illustrative demo data, not live measurements`}
          action={
            <span className="text-[10px] font-bold tracking-widest text-[#c2c9c1]">
              •••
            </span>
          }
        >
          <div className="mb-2 flex gap-4 text-[10px] font-semibold text-[#79847c]">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#37866a]" /> Units sold
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#df9860]" /> Waste units
            </span>
          </div>
          <div className="h-[220px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="soldFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#37866a" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#37866a" stopOpacity={0.01} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e8ece7" />
                <XAxis
                  dataKey="day"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#818b83", fontSize: 11 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#818b83", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: "1px solid #e6e8e3",
                    fontSize: 11,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="sold"
                  name="Units sold"
                  stroke="#37866a"
                  strokeWidth={2.5}
                  fill="url(#soldFill)"
                />
                <Area
                  type="monotone"
                  dataKey="waste"
                  name="Waste units"
                  stroke="#df9860"
                  strokeWidth={2}
                  fill="none"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title="Freshness watch"
          subtitle="Example batches requiring attention"
          action={
            <GhostButton onClick={() => onNavigate("inventory")}>View all →</GhostButton>
          }
        >
          <div className="flex flex-col">
            {freshness.length === 0 ? (
              <EmptyState title="No freshness concerns" />
            ) : (
              freshness.map((f) => (
                <FreshnessRow key={f.name} {...f} />
              ))
            )}
          </div>
          <GhostButton
            className="mt-3 w-full justify-center"
            onClick={() => onNavigate("inventory")}
          >
            Open inventory →
          </GhostButton>
        </Panel>
      </div>

      {/* Activity + recommendations */}
      <div className="mb-5 grid gap-4 xl:grid-cols-2">
        <Panel title="Recent operational activity" subtitle="Simulated demo log, not a system audit trail">
          <ul className="flex flex-col gap-2.5">
            {activity.map((a, i) => (
              <li key={i} className="flex items-baseline gap-3 text-[11px]">
                <span className="w-14 shrink-0 text-right font-mono text-[9px] text-[#9aa39b]">
                  {a.time}
                </span>
                <span className="min-w-0 text-[#5c6b62]">{a.text}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel
          title="Recommendations awaiting manager review"
          subtitle="Illustrative proposals only — no actions have been executed"
          action={
            <GhostButton onClick={() => onNavigate("recommendations")}>
              View all 4 →
            </GhostButton>
          }
        >
          <div className="flex flex-col divide-y divide-[#eff1ed]">
            <RecRow
              tone="amber"
              title="Markdown whole milk at Store Central"
              desc="20 units expire tomorrow · expected demand is below batch quantity."
              tag="Markdown"
              value="15% off"
              onReview={() => onNavigate("recommendations")}
            />
            <RecRow
              tone="green"
              title="Transfer leafy greens to Store South"
              desc="Surplus at Store North · receiving store has forecasted demand."
              tag="Transfer"
              value="18 units"
              onReview={() => onNavigate("recommendations")}
            />
            <RecRow
              tone="violet"
              title="Reduce next yogurt replenishment"
              desc="Current stock and inbound receipt may exceed expected demand."
              tag="Replenish"
              value="−12 units"
              onReview={() => onNavigate("recommendations")}
            />
          </div>
        </Panel>
      </div>
    </>
  );
}

/* ---------- Row subcomponents ---------- */

function FreshnessRow({
  emoji,
  name,
  store,
  qty,
  expiry,
  risk,
}: (typeof freshness)[number]) {
  return (
    <div className="flex items-center gap-3 border-b border-[#eff1ed] py-2.5 last:border-0">
      <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-[#f5f5ed] text-lg">
        {emoji}
      </div>
      <div className="min-w-0 flex-1">
        <strong className="block truncate text-[11px] text-[#3d4a40]">{name}</strong>
        <small className="block truncate text-[9.5px] text-[#9aa39b]">{store}</small>
        <p className="mt-0.5 text-[10px] text-[#7f8a81]">
          {qty} · {expiry}
        </p>
      </div>
      <Badge tone={risk === "high" ? "red" : "amber"}>{risk}</Badge>
    </div>
  );
}

function RecRow({
  tone,
  title,
  desc,
  tag,
  value,
  onReview,
}: {
  tone: "amber" | "green" | "violet";
  title: string;
  desc: string;
  tag: string;
  value: string;
  onReview: () => void;
}) {
  const badgeTone: BadgeTone = tone === "amber" ? "amber" : tone === "green" ? "green" : "violet";
  return (
    <div className="flex flex-wrap items-center gap-2.5 py-3">
      <span
        className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg text-sm font-black ${
          tone === "amber"
            ? "bg-[#fff0e4] text-[#b8753d]"
            : tone === "green"
              ? "bg-[#eaf5ec] text-[#37815b]"
              : "bg-[#f1edff] text-[#816ac1]"
        }`}
      >
        {tone === "amber" ? "%" : tone === "green" ? "⇄" : "＋"}
      </span>
      <div className="min-w-[150px] flex-1">
        <strong className="block text-[11px] text-[#39483d]">{title}</strong>
        <p className="mt-0.5 text-[10px] leading-relaxed text-[#8c978e]">{desc}</p>
      </div>
      <Badge tone={badgeTone}>{tag}</Badge>
      <div className="min-w-[68px] text-right">
        <strong className="block text-[11px] text-[#39483d]">{value}</strong>
        <small className="block text-[9px] text-[#9aa39b]">Proposed</small>
      </div>
      <Badge tone="outline">{tag}</Badge>
      <GhostButton onClick={onReview}>Review</GhostButton>
      {tone === "amber" && (
        <span className="sr-only">
          <AlertTriangle size={1} />
        </span>
      )}
    </div>
  );
}
