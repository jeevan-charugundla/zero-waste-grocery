import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
  Line,
  LineChart,
} from "recharts";
import { Leaf, IndianRupee, Heart, Trash2 } from "lucide-react";
import { PageHeader, Panel, KpiCard, Badge, Select } from "../components/ui";
import { DemoBadge } from "../components/ui";

const periods = [
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last quarter" },
] as const;

const wpsData = [
  { week: "W1", prevented: 42, wasted: 18 },
  { week: "W2", prevented: 55, wasted: 15 },
  { week: "W3", prevented: 61, wasted: 14 },
  { week: "W4", prevented: 74, wasted: 11 },
];

const rateData = [
  { week: "W1", rate: 6.1 },
  { week: "W2", rate: 5.4 },
  { week: "W3", rate: 4.9 },
  { week: "W4", rate: 4.8 },
];

const markdowns = [
  { id: "m1", product: "Whole Milk 1L", units: 17, recovered: "₹510", status: "Sold through" },
  { id: "m2", product: "Strawberries 250g", units: 9, recovered: "₹318", status: "Sold through" },
  { id: "m3", product: "Whole Wheat Bread", units: 22, recovered: "₹494", status: "Sold through" },
  { id: "m4", product: "Greek Yogurt 500g", units: 0, recovered: "₹0", status: "In progress" },
];

export default function ImpactPage() {
  const [period, setPeriod] = useState<(typeof periods)[number]["value"]>("7d");
  const periodLabel = periods.find((p) => p.value === period)?.label ?? "";

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="Impact & analytics"
        subtitle="Sustainability and financial outcomes of your zero-waste program. Values shown as 'Estimated' are simulated for demonstration; do not treat them as verified savings."
        action={
          <>
            <Select ariaLabel="Impact period" value={period} onChange={setPeriod} options={periods} />
            <DemoBadge />
          </>
        }
      />

      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Food waste prevented"
          value="232 units"
          change="Estimated"
          changeTone="neutral"
          note="4-week demo window"
          icon={<Leaf size={15} />}
          explanation="Units moved through markdown, transfer, bundles, or donation rather than being discarded. Simulated demo value."
        />
        <KpiCard
          label="Waste rate trend"
          value="6.1% → 4.8%"
          change="↓ 1.3 pts"
          changeTone="green"
          note="vs. Week 1 (demo series)"
          icon={<Leaf size={15} />}
        />
        <KpiCard
          label="Estimated financial impact"
          value="₹1,322"
          change="Simulated"
          changeTone="neutral"
          note="recovered markdown value"
          icon={<IndianRupee size={15} />}
          explanation="Simulated based on demo markdown sales only. Not validated against real accounting."
        />
        <KpiCard
          label="Donated units"
          value={`${seedTotalDonated()} units`}
          change="Measured route"
          changeTone="neutral"
          note="local demo log"
          icon={<Heart size={15} />}
        />
      </div>

      <div className="mb-5 grid gap-4 xl:grid-cols-2">
        <Panel title="Prevented vs wasted units" subtitle={`${periodLabel} · simulated demo series`}>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={wpsData} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e8ece7" />
                <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: "#818b83", fontSize: 11 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: "#818b83", fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e6e8e3", fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="prevented" name="Prevented" fill="#37866a" radius={[4, 4, 0, 0]} />
                <Bar dataKey="wasted" name="Wasted" fill="#df9860" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Waste rate trend" subtitle={`${periodLabel} · simulated demo series`}>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rateData} margin={{ top: 10, right: 12, left: -22, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e8ece7" />
                <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: "#818b83", fontSize: 11 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: "#818b83", fontSize: 11 }} unit="%" />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e6e8e3", fontSize: 11 }} />
                <Line type="monotone" dataKey="rate" name="Waste rate" stroke="#287452" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel
          title="Markdown recovery summary"
          subtitle="Simulated inventory recovery via discounted sales"
        >
          <div className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
            <table className="w-full min-w-[380px] text-left">
              <thead>
                <tr className="border-b border-[#eef0ec] text-left text-[10px] font-bold uppercase tracking-wider text-[#9aa39b]">
                  <th className="py-2.5 pr-3">Product</th>
                  <th className="py-2.5 pr-3 text-right">Units</th>
                  <th className="py-2.5 pr-3 text-right">Recovered (est.)</th>
                  <th className="py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eff1ed]">
                {markdowns.map((m) => (
                  <tr key={m.id} className="text-[11px] text-[#5c6b62] hover:bg-[#fafbfa]">
                    <td className="py-2.5 pr-3 font-semibold text-[#39473d]">{m.product}</td>
                    <td className="py-2.5 pr-3 text-right">{m.units}</td>
                    <td className="py-2.5 pr-3 text-right">{m.recovered}</td>
                    <td className="py-2.5">
                      <Badge tone={m.status === "Sold through" ? "green" : "neutral"}>{m.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[10px] italic text-[#a9b1a9]">
            Simulated demo values — not verified financial records.
          </p>
        </Panel>

        <Panel title="Donation & disposal summary" subtitle="Local demo activity log">
          <ul className="flex flex-col gap-3 text-[11px] text-[#5c6b62]">
            <li className="flex items-start gap-2.5">
              <Heart size={13} className="mt-0.5 shrink-0 text-green-700" />
              <span>
                <b className="text-[#39473d]">42 units donated</b> to 2 local partners this month
                <br />
                <span className="text-[10px] text-[#9aa39b]">Local demo log — not a verified charitable record.</span>
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <Trash2 size={13} className="mt-0.5 shrink-0 text-[#b45e48]" />
              <span>
                <b className="text-[#39473d]">10 units safely disposed</b> across 2 expired batch groups
                <br />
                <span className="text-[10px] text-[#9aa39b]">Disposal-only items never enter the donation route.</span>
              </span>
            </li>
            <li className="flex items-start gap-2.5">
              <Leaf size={13} className="mt-0.5 shrink-0 text-[#287452]" />
              <span>
                <b className="text-[#39473d]">Zero edible donations expired or unsafe</b>
                <br />
                <span className="text-[10px] text-[#9aa39b]">All flagged unsafe batches were routed to disposal.</span>
              </span>
            </li>
          </ul>
        </Panel>
      </div>
    </>
  );
}

function seedTotalDonated(): number {
  return 42;
}
