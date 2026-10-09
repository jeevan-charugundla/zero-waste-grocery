import { useMemo, useState } from "react";
import { Check, X, Pencil, Sparkles, ClipboardList } from "lucide-react";
import {
  PageHeader,
  Panel,
  KpiCard,
  Badge,
  GhostButton,
  PrimaryButton,
  EmptyState,
  type BadgeTone,
} from "../components/ui";
import { DemoBadge } from "../components/ui";

/* ---------- Types ---------- */

type Action = "markdown" | "transfer" | "replenish" | "donate" | "bundle";
type Status = "pending" | "approved" | "rejected";
type Urgency = "high" | "medium" | "low";

interface Recommendation {
  id: string;
  product: string;
  action: Action;
  actionLabel: string;
  rationale: string;
  urgency: Urgency;
  status: Status;
  evidence: string;
  estimatedImpact: string;
}

/* ---------- Illustrative demo data ---------- */

const seed: Recommendation[] = [
  {
    id: "r1",
    product: "Whole Milk 1L · Batch M-104",
    action: "markdown",
    actionLabel: "Markdown 15%",
    rationale:
      "20 units expire tomorrow and forecast demand covers only 8 units before expiry.",
    urgency: "high",
    status: "pending",
    evidence: "Forecast 8 units sold by expiry · 20 on hand · 1 day remaining",
    estimatedImpact: "≈ ₹340 recovered vs. zero if unsold",
  },
  {
    id: "r2",
    product: "Leafy Greens · Across stores",
    action: "transfer",
    actionLabel: "Transfer 18 units",
    rationale:
      "Surplus at Store North; Store South has forecasted demand exceeding current stock.",
    urgency: "medium",
    status: "pending",
    evidence: "Store North surplus 24 units · Store South deficit 18 units",
    estimatedImpact: "Avoids ≈ ₹620 waste",
  },
  {
    id: "r3",
    product: "Greek Yogurt 500g",
    action: "replenish",
    actionLabel: "Reduce next order",
    rationale:
      "Current stock plus inbound receipt exceeds expected demand for the next 7 days.",
    urgency: "low",
    status: "pending",
    evidence: "75 tubs on hand · forecast 16/day · inbound 40 tubs",
    estimatedImpact: "Avoids over-order by 12 units",
  },
  {
    id: "r4",
    product: "Whole Wheat Bread · Batch BR-552",
    action: "bundle",
    actionLabel: "Add to bundle",
    rationale:
      "58 loaves with 4 days to expiry pair well with oats in a value bundle.",
    urgency: "low",
    status: "pending",
    evidence: "58 loaves · 4 day expiry · oats pair (long shelf-life)",
    estimatedImpact: "≈ ₹810 recovered in bundle sales",
  },
];

/* ---------- Filters ---------- */

const urgencyOpts = ["All", "High", "Medium", "Low"] as const;
const typeOpts = ["All", "Markdown", "Transfer", "Replenish", "Bundle"] as const;
const statusOpts = ["All", "Pending", "Approved", "Rejected"] as const;

/* ---------- Page ---------- */

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<Recommendation[]>(seed);
  const [urgency, setUrgency] = useState<(typeof urgencyOpts)[number]>("All");
  const [type, setType] = useState<(typeof typeOpts)[number]>("All");
  const [status, setStatus] = useState<(typeof statusOpts)[number]>("All");
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [toast, setToast] = useState<string | null>(null);

  const filtered = useMemo(
    () =>
      recs.filter((r) => {
        if (
          urgency === "High" && r.urgency !== "high" ||
          urgency === "Medium" && r.urgency !== "medium" ||
          urgency === "Low" && r.urgency !== "low"
        )
          return false;
        if (
          type === "Markdown" && r.action !== "markdown" ||
          type === "Transfer" && r.action !== "transfer" ||
          type === "Replenish" && r.action !== "replenish" ||
          type === "Bundle" && r.action !== "bundle"
        )
          return false;
        if (
          status === "Pending" && r.status !== "pending" ||
          status === "Approved" && r.status !== "approved" ||
          status === "Rejected" && r.status !== "rejected"
        )
          return false;
        return true;
      }),
    [recs, urgency, type, status]
  );

  const counts = useMemo(
    () => ({
      pending: recs.filter((r) => r.status === "pending").length,
      approved: recs.filter((r) => r.status === "approved").length,
      rejected: recs.filter((r) => r.status === "rejected").length,
    }),
    [recs]
  );

  const flash = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2600);
  };

  const approve = (id: string) => {
    setRecs((rs) => rs.map((r) => (r.id === id ? { ...r, status: "approved" } : r)));
    flash("Demo action: recommendation approved in local state only. No real inventory or pricing change has occurred.");
  };
  const reject = (id: string) => {
    setRecs((rs) => rs.map((r) => (r.id === id ? { ...r, status: "rejected" } : r)));
    flash("Demo action: recommendation rejected in local state only. No real change has occurred.");
  };
  const saveEdit = (id: string) => {
    setRecs((rs) =>
      rs.map((r) => (r.id === id ? { ...r, actionLabel: editValue || r.actionLabel } : r))
    );
    setEditing(null);
    flash("Demo action: recommendation edited in local state only.");
  };

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="AI recommendations"
        subtitle="Review, approve, or reject suggested actions generated for your perishable inventory. Approve and reject controls here are local demo interactions — no real inventory, pricing, or transfer operation is executed."
        action={<DemoBadge />}
      />

      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Pending" value={String(counts.pending)} note="awaiting your review" icon={<ClipboardList size={15} />} />
        <KpiCard label="Approved" value={String(counts.approved)} change="Demo only" changeTone="neutral" note="local state" icon={<Check size={15} />} />
        <KpiCard label="Rejected" value={String(counts.rejected)} change="Demo only" changeTone="neutral" note="local state" icon={<X size={15} />} />
        <KpiCard
          label="Potential impact"
          value="₹1,770"
          change="Estimated"
          changeTone="neutral"
          note="if all approved (demo estimate)"
          icon={<Sparkles size={15} />}
        />
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-2.5">
        {[
          { label: " Urgency", value: urgency, setter: setUrgency, opts: urgencyOpts as readonly string[] },
          { label: "Type", value: type, setter: setType, opts: typeOpts as readonly string[] },
          { label: "Status", value: status, setter: setStatus, opts: statusOpts as readonly string[] },
        ].map(({ label, value, setter, opts }) => (
          <select
            key={label}
            value={value}
            onChange={(e) =>
              (setter as (v: string) => void)(e.target.value)
            }
            aria-label={`Filter by ${label.toLowerCase()}`}
            className="rounded-lg border border-[#e4e9e2] bg-white px-2.5 py-2 text-[11px] font-semibold text-[#45614e] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
          >
            {opts.map((o) => (
              <option key={o}>{o}</option>
            ))}
          </select>
        ))}
        {(urgency !== "All" || type !== "All" || status !== "All") && (
          <GhostButton
            onClick={() => {
              setUrgency("All");
              setType("All");
              setStatus("All");
            }}
          >
            Clear filters
          </GhostButton>
        )}
      </div>

      {/* Recommendation cards */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={<Sparkles size={20} />}
          title="No recommendations match your filters"
          description="Adjust the urgency, type, or status filters to see more proposals."
        />
      ) : (
        <div className="flex flex-col gap-3.5">
          {filtered.map((r) => (
            <Panel key={r.id}>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start">
                {/* Icon + text */}
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#f1f5f0] text-[#578066]">
                      <Sparkles size={14} />
                    </span>
                    <strong className="text-[12.5px] text-[#39483d]">{r.product}</strong>
                    <Badge
                      tone={
                        r.urgency === "high" ? "red" : r.urgency === "medium" ? "amber" : "neutral"
                      }
                    >
                      {r.urgency} urgency
                    </Badge>
                    <Badge tone={statusBadgeTone(r.status)}>{r.actionLabel}</Badge>
                  </div>
                  <p className="mt-1.5 text-[11px] leading-relaxed text-[#8c978e]">{r.rationale}</p>
                  {editing === r.id ? (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <input
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        placeholder="Edited action, e.g. Markdown 20%"
                        aria-label="Edit recommendation action (demo only)"
                        className="min-w-[180px] rounded-lg border border-[#e4e9e2] bg-white px-2.5 py-1.5 text-[11px] text-[#39473d] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
                      />
                      <PrimaryButton onClick={() => saveEdit(r.id)} className="py-1.5">
                        Save
                      </PrimaryButton>
                      <GhostButton onClick={() => setEditing(null)}>Cancel</GhostButton>
                    </div>
                  ) : (
                    <p className="mt-2 text-[10.5px] text-[#9aa39b]">
                      <b className="font-semibold text-[#5c6b62]">Evidence:</b> {r.evidence} ·{" "}
                      <b className="font-semibold text-[#5c6b62]">Impact:</b> {r.estimatedImpact}{" "}
                      <em className="text-[#a9b1a9]">(demo estimate — no confidence score claimed)</em>
                    </p>
                  )}
                </div>

                {/* Controls */}
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  {r.status === "pending" ? (
                    <>
                      <PrimaryButton onClick={() => approve(r.id)} className="py-1.5">
                        <Check size={13} /> Approve
                      </PrimaryButton>
                      <GhostButton onClick={() => reject(r.id)}>
                        <X size={13} /> Reject
                      </GhostButton>
                    </>
                  ) : (
                    <Badge tone={r.status === "approved" ? "green" : "red"}>
                      {r.status === "approved" ? "Approved (demo)" : "Rejected (demo)"}
                    </Badge>
                  )}
                  {editing === r.id ? null : (
                    <GhostButton
                      onClick={() => {
                        setEditing(r.id);
                        setEditValue(r.actionLabel);
                      }}
                    >
                      <Pencil size={12} /> Edit
                    </GhostButton>
                  )}
                </div>
              </div>
            </Panel>
          ))}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div
          role="status"
          className="fixed bottom-5 right-5 z-50 max-w-xs rounded-xl border border-[#cfe7d8] bg-white px-4 py-3 text-[11px] font-medium text-[#1b6143] shadow-lg"
        >
          {toast}
        </div>
      )}
    </>
  );
}

function statusBadgeTone(s: Status): BadgeTone {
  return s === "approved" ? "green" : s === "rejected" ? "red" : "outline";
}
