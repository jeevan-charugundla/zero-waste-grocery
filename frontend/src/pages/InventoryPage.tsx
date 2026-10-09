import { useMemo, useState } from "react";
import { Search, X, Filter } from "lucide-react";
import {
  PageHeader,
  Panel,
  KpiCard,
  Badge,
  GhostButton,
  EmptyState,
  type BadgeTone,
} from "../components/ui";
import { DemoBadge } from "../components/ui";

/* ---------- Types ---------- */

type Freshness = "healthy" | "approaching" | "critical";
type StockStatus = "ok" | "low" | "excess";

interface InventoryItem {
  id: string;
  product: string;
  category: string;
  sku: string;
  batch: string;
  available: number;
  unit: string;
  expiryDays: number;
  expiryDate: string;
  freshness: Freshness;
  stock: StockStatus;
}

/* ---------- Illustrative demo data ---------- */

const inventory: InventoryItem[] = [
  {
    id: "1",
    product: "Whole Milk 1L",
    category: "Dairy",
    sku: "DEMO-MILK-1L",
    batch: "M-104",
    available: 20,
    unit: "units",
    expiryDays: 1,
    expiryDate: "2026-10-10",
    freshness: "critical",
    stock: "ok",
  },
  {
    id: "2",
    product: "Strawberries 250g",
    category: "Produce",
    sku: "DEMO-STRAW-250",
    batch: "S-221",
    available: 14,
    unit: "packs",
    expiryDays: 2,
    expiryDate: "2026-10-11",
    freshness: "critical",
    stock: "ok",
  },
  {
    id: "3",
    product: "Baby Spinach 200g",
    category: "Produce",
    sku: "DEMO-SPIN-200",
    batch: "SP-011",
    available: 3,
    unit: "packs",
    expiryDays: 1,
    expiryDate: "2026-10-10",
    freshness: "critical",
    stock: "low",
  },
  {
    id: "4",
    product: "Greek Yogurt 500g",
    category: "Dairy",
    sku: "DEMO-YOG-500",
    batch: "Y-089",
    available: 75,
    unit: "tubs",
    expiryDays: 10,
    expiryDate: "2026-10-19",
    freshness: "approaching",
    stock: "excess",
  },
  {
    id: "5",
    product: "Whole Wheat Bread",
    category: "Bakery",
    sku: "DEMO-BREAD-WW",
    batch: "BR-552",
    available: 58,
    unit: "loaves",
    expiryDays: 4,
    expiryDate: "2026-10-13",
    freshness: "approaching",
    stock: "excess",
  },
  {
    id: "6",
    product: "Free Range Eggs 12pk",
    category: "Dairy",
    sku: "DEMO-EGG-12",
    batch: "E-301",
    available: 4,
    unit: "cartons",
    expiryDays: 14,
    expiryDate: "2026-10-23",
    freshness: "healthy",
    stock: "low",
  },
  {
    id: "7",
    product: "Rolled Oats 500g",
    category: "Grains",
    sku: "DEMO-OATS-500",
    batch: "O-774",
    available: 38,
    unit: "packs",
    expiryDays: 355,
    expiryDate: "2027-09-30",
    freshness: "healthy",
    stock: "ok",
  },
  {
    id: "8",
    product: "Whole Grain Pasta 500g",
    category: "Grains",
    sku: "DEMO-PASTA-500",
    batch: "P-220",
    available: 33,
    unit: "packs",
    expiryDays: 720,
    expiryDate: "2028-09-22",
    freshness: "healthy",
    stock: "ok",
  },
];

const categories = ["All", "Dairy", "Produce", "Bakery", "Grains"] as const;
const freshnessOpts = ["All", "Healthy", "Approaching expiry", "Critical"] as const;
const stockOpts = ["All", "OK", "Low stock", "Excess"] as const;

/* ---------- Page ---------- */

export default function InventoryPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<(typeof categories)[number]>("All");
  const [freshFilter, setFreshFilter] = useState<(typeof freshnessOpts)[number]>("All");
  const [stockFilter, setStockFilter] = useState<(typeof stockOpts)[number]>("All");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return inventory.filter((it) => {
      if (q && !(`${it.product} ${it.sku}`.toLowerCase().includes(q))) return false;
      if (category !== "All" && it.category !== category) return false;
      if (
        freshFilter === "Healthy" && it.freshness !== "healthy" ||
        freshFilter === "Approaching expiry" && it.freshness !== "approaching" ||
        freshFilter === "Critical" && it.freshness !== "critical"
      )
        return false;
      if (
        stockFilter === "OK" && it.stock !== "ok" ||
        stockFilter === "Low stock" && it.stock !== "low" ||
        stockFilter === "Excess" && it.stock !== "excess"
      )
        return false;
      return true;
    });
  }, [query, category, freshFilter, stockFilter]);

  const summary = useMemo(
    () => ({
      totalSkus: inventory.length,
      nearExpiry: inventory.filter((i) => i.expiryDays <= 3).length,
      lowStock: inventory.filter((i) => i.stock === "low").length,
      excess: inventory.filter((i) => i.stock === "excess").length,
    }),
    []
  );

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="Inventory & expiry"
        subtitle="Track every batch's freshness, stock level, and expiry timing across your grocery network. Use the filters below to focus on what needs attention today."
        action={<DemoBadge />}
      />

      {/* Summary cards */}
      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Total SKUs"
          value={String(summary.totalSkus)}
          note="in this demo workspace"
          icon={<Filter size={15} />}
        />
        <KpiCard
          label="Near expiry"
          value={String(summary.nearExpiry)}
          change="≤ 3 days"
          changeTone="amber"
          note="batch groups"
          icon={<Badge tone="amber" className="pointer-events-none">⚠</Badge>}
        />
        <KpiCard
          label="Low stock"
          value={String(summary.lowStock)}
          change="Replenish"
          changeTone="amber"
          note="SKUs"
          icon={<Badge tone="neutral" className="pointer-events-none">↓</Badge>}
        />
        <KpiCard
          label="Excess inventory"
          value={String(summary.excess)}
          change="Markdown"
          changeTone="neutral"
          note="SKUs"
          icon={<Badge tone="neutral" className="pointer-events-none">↑</Badge>}
        />
      </div>

      {/* Search + filters */}
      <div className="mb-4 flex flex-wrap items-center gap-2.5">
        <div className="relative min-w-[220px] flex-1 sm:max-w-xs">
          <Search
            size={14}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#9aa39b]"
          />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search product name or SKU…"
            aria-label="Search by product name or SKU"
            className="w-full rounded-lg border border-[#e4e9e2] bg-white py-2 pl-9 pr-8 text-[12px] text-[#39473d] placeholder:text-[#a9b1a9] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-full p-0.5 text-[#9aa39b] hover:bg-[#f1f5f0]"
              aria-label="Clear search"
            >
              <X size={13} />
            </button>
          )}
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as typeof category)}
          aria-label="Filter by category"
          className="rounded-lg border border-[#e4e9e2] bg-white px-2.5 py-2 text-[11px] font-semibold text-[#45614e] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
        >
          {categories.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <select
          value={freshFilter}
          onChange={(e) => setFreshFilter(e.target.value as (typeof freshnessOpts)[number])}
          aria-label="Filter by freshness"
          className="rounded-lg border border-[#e4e9e2] bg-white px-2.5 py-2 text-[11px] font-semibold text-[#45614e] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
        >
          {freshnessOpts.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <select
          value={stockFilter}
          onChange={(e) => setStockFilter(e.target.value as (typeof stockOpts)[number])}
          aria-label="Filter by stock status"
          className="rounded-lg border border-[#e4e9e2] bg-white px-2.5 py-2 text-[11px] font-semibold text-[#45614e] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
        >
          {stockOpts.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <Panel
        title={`Inventory (${filtered.length} of ${inventory.length})`}
        subtitle="Local demo records · not connected to live inventory"
      >
        {filtered.length === 0 ? (
          <EmptyState
            title="No products match your filters"
            description="Try clearing a filter or adjusting the search term."
          />
        ) : (
          <OverflowTable>
          <thead>
            <tr className="border-b border-[#eef0ec] text-left text-[10px] font-bold uppercase tracking-wider text-[#9aa39b]">
              <th className="py-2.5 pr-3">Product</th>
              <th className="py-2.5 pr-3">SKU / Category</th>
              <th className="py-2.5 pr-3 text-right">Available</th>
              <th className="py-2.5 pr-3">Batch</th>
              <th className="py-2.5 pr-3">Expiry</th>
              <th className="py-2.5 pr-3">Freshness</th>
              <th className="py-2.5 pr-3">Stock</th>
              <th className="py-2.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#eff1ed]">
            {filtered.map((it) => (
              <tr key={it.id} className="text-[11px] text-[#5c6b62] hover:bg-[#fafbfa]">
                <td className="py-2.5 pr-3 font-semibold text-[#39473d]">{it.product}</td>
                <td className="py-2.5 pr-3">
                  <span className="block font-mono text-[10px] text-[#889390]">{it.sku}</span>
                  <span className="text-[10px] text-[#a9b1a9]">{it.category}</span>
                </td>
                <td className="py-2.5 pr-3 text-right font-semibold text-[#39473d]">
                  {it.available}
                  <span className="ml-1 text-[10px] font-normal text-[#9aa39b]">{it.unit}</span>
                </td>
                <td className="py-2.5 pr-3 font-mono text-[10px] text-[#889390]">{it.batch}</td>
                <td className="py-2.5 pr-3">
                  <span className="block text-[11px]">{it.expiryDate}</span>
                  <span
                    className={`text-[10px] ${
                      it.expiryDays <= 2
                        ? "font-semibold text-red-600"
                        : it.expiryDays <= 5
                          ? "font-semibold text-amber-700"
                          : "text-[#9aa39b]"
                    }`}
                  >
                    {it.expiryDays === 1 ? "in 1 day" : `in ${it.expiryDays} days`}
                  </span>
                </td>
                <td className="py-2.5 pr-3">
                  <FreshnessBadge freshness={it.freshness} />
                </td>
                <td className="py-2.5 pr-3">
                  <StockBadge stock={it.stock} />
                </td>
                <td className="py-2.5 text-right">
                  <GhostButton onClick={() => alert(`Demo action: would open detail view for ${it.product} (batch ${it.batch}). No real inventory change is made.`)}>
                    Detail
                  </GhostButton>
                </td>
              </tr>
            ))}
          </tbody>
          </OverflowTable>
        )}
      </Panel>
    </>
  );
}

/* ---------- Badges ---------- */

function FreshnessBadge({ freshness }: { freshness: Freshness }) {
  const tone: BadgeTone =
    freshness === "critical" ? "red" : freshness === "approaching" ? "amber" : "green";
  const label =
    freshness === "critical"
      ? "Critical"
      : freshness === "approaching"
        ? "Approaching"
        : "Healthy";
  return <Badge tone={tone}>{label}</Badge>;
}

function StockBadge({ stock }: { stock: StockStatus }) {
  const tone: BadgeTone = stock === "low" ? "amber" : stock === "excess" ? "violet" : "green";
  const label = stock === "low" ? "Low stock" : stock === "excess" ? "Excess" : "OK";
  return <Badge tone={tone}>{label}</Badge>;
}

/* ---------- Table overflow helper ---------- */

function OverflowTable({ children }: { children: React.ReactNode }) {
  return (
    <div className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
      <table className="w-full min-w-[720px] text-left">{children}</table>
    </div>
  );
}
