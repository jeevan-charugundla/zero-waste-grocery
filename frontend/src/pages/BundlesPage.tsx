import { useMemo, useState } from "react";
import { Package, Check, X, Eye, Percent } from "lucide-react";
import {
  PageHeader,
  Panel,
  KpiCard,
  Badge,
  GhostButton,
  PrimaryButton,
  EmptyState,
} from "../components/ui";
import { DemoBadge } from "../components/ui";

type BundleStatus = "proposed" | "approved" | "rejected";

interface Bundle {
  id: string;
  title: string;
  products: { emoji: string; name: string; available: number; urgency: string }[];
  price: number | null;
  discount: number | null;
  urgencyReason: string;
  status: BundleStatus;
}

const seedBundles: Bundle[] = [
  {
    id: "b1",
    title: "Breakfast value pack",
    products: [
      { emoji: "🥛", name: "Whole Milk 1L", available: 20, urgency: "Expires tomorrow" },
      { emoji: "🍞", name: "Whole Wheat Bread", available: 58, urgency: "4 days to expiry" },
      { emoji: "🥣", name: "Greek Yogurt 500g", available: 75, urgency: "Excess stock" },
    ],
    price: 149,
    discount: 20,
    urgencyReason: "Milk expires tomorrow; bread and yogurt are slow movers this week.",
    status: "proposed",
  },
  {
    id: "b2",
    title: "Fresh fruit duo",
    products: [
      { emoji: "🍓", name: "Strawberries 250g", available: 14, urgency: "Expires in 2 days" },
      { emoji: "🍌", name: "Bananas 1kg", available: 32, urgency: "Ripening rapidly" },
    ],
    price: 129,
    discount: 15,
    urgencyReason: "Both items lose shelf appeal within 48 hours at current temperatures.",
    status: "proposed",
  },
  {
    id: "b3",
    title: "Pantry staple combo",
    products: [
      { emoji: "🌾", name: "Rolled Oats 500g", available: 38, urgency: "Long shelf life" },
      { emoji: "🍝", name: "Whole Grain Pasta 500g", available: 33, urgency: "Long shelf life" },
    ],
    price: 119,
    discount: 10,
    urgencyReason: "No freshness pressure — proposed to lift basket size, not rescue expiring stock.",
    status: "proposed",
  },
];

export default function BundlesPage() {
  const [bundles, setBundles] = useState<Bundle[]>(seedBundles);
  const [preview, setPreview] = useState<Bundle | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const counts = useMemo(
    () => ({
      proposed: bundles.filter((b) => b.status === "proposed").length,
      approved: bundles.filter((b) => b.status === "approved").length,
      rejected: bundles.filter((b) => b.status === "rejected").length,
    }),
    [bundles]
  );

  const estimatedRecovery = useMemo(() => {
    const r = bundles
      .filter((b) => b.status === "approved" && b.price !== null)
      .reduce((s, b) => s + (b.price ?? 0), 0);
    return r;
  }, [bundles]);

  const flash = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2600);
  };

  const setBundleStatus = (id: string, status: BundleStatus, verb: string) => {
    setBundles((bs) => bs.map((b) => (b.id === id ? { ...b, status } : b)));
    flash(`Demo action: bundle ${verb} in local state only. No real promotion or bundle was created.`);
  };

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="Smart bundles"
        subtitle="Combine suitable products into value packs that move slow or at-risk stock faster. Prices and discounts below are illustrative; bundle approval here is a local demo interaction and creates no real promotion."
        action={<DemoBadge />}
      />

      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Proposed bundles" value={String(counts.proposed)} note="awaiting review" icon={<Package size={15} />} />
        <KpiCard label="Approved (demo)" value={String(counts.approved)} change="Local state" changeTone="neutral" note="not published" icon={<Check size={15} />} />
        <KpiCard label="Rejected (demo)" value={String(counts.rejected)} change="Local state" changeTone="neutral" note="not published" icon={<X size={15} />} />
        <KpiCard
          label="Potential recovery"
          value={counts.approved > 0 ? `₹${estimatedRecovery}` : "—"}
          change="Estimated"
          changeTone="neutral"
          note="if approved bundles sold through (demo)"
          icon={<Percent size={15} />}
        />
      </div>

      {bundles.length === 0 ? (
        <EmptyState icon={<Package size={20} />} title="No bundles proposed" />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {bundles.map((b) => (
            <Panel key={b.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <strong className="text-[13px] text-[#39473d]">{b.title}</strong>
                    <Badge
                      tone={
                        b.status === "approved" ? "green" : b.status === "rejected" ? "red" : "outline"
                      }
                    >
                      {b.status === "approved"
                        ? "Approved (demo)"
                        : b.status === "rejected"
                          ? "Rejected (demo)"
                          : "Proposed"}
                    </Badge>
                  </div>
                  <p className="mt-1 text-[11px] leading-relaxed text-[#8c978e]">{b.urgencyReason}</p>
                </div>
              </div>

              {/* Products */}
              <ul className="mt-3 flex flex-col divide-y divide-[#eff1ed]">
                {b.products.map((p) => (
                  <li key={p.name} className="flex items-center gap-2.5 py-2">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#f5f5ed] text-base">
                      {p.emoji}
                    </span>
                    <span className="min-w-0 flex-1 text-[11.5px] font-semibold text-[#39473d]">
                      {p.name}
                    </span>
                    <span className="text-[10px] font-semibold text-[#7f8a81]">{p.available} available</span>
                    <Badge tone={p.urgency.startsWith("Expires") ? "red" : p.urgency.startsWith("4") || p.urgency.startsWith("Ripen") ? "amber" : "neutral"}>
                      {p.urgency}
                    </Badge>
                  </li>
                ))}
              </ul>

              {/* Pricing + actions */}
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2.5 border-t border-[#eff1ed] pt-3">
                <div className="flex items-baseline gap-2 text-[11px] text-[#5c6b62]">
                  {b.price !== null ? (
                    <>
                      <strong className="text-[14px] font-bold text-[#24372b]">₹{b.price}</strong>
                      {b.discount !== null && (
                        <Badge tone="amber">
                          {b.discount}% off combined
                        </Badge>
                      )}
                      <em className="text-[#a9b1a9]">(illustrative pricing)</em>
                    </>
                  ) : (
                    <em className="text-[#a9b1a9]">Pricing not suggested (no supporting data)</em>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <GhostButton onClick={() => setPreview(b)}>
                    <Eye size={12} /> Preview
                  </GhostButton>
                  {b.status === "proposed" ? (
                    <>
                      <PrimaryButton onClick={() => setBundleStatus(b.id, "approved", "approved")} className="py-1.5">
                        <Check size={13} /> Approve
                      </PrimaryButton>
                      <GhostButton onClick={() => setBundleStatus(b.id, "rejected", "rejected")}>
                        <X size={13} /> Reject
                      </GhostButton>
                    </>
                  ) : (
                    <Badge tone={b.status === "approved" ? "green" : "red"}>
                      {b.status === "approved" ? "Approved (demo)" : "Rejected (demo)"}
                    </Badge>
                  )}
                </div>
              </div>
            </Panel>
          ))}
        </div>
      )}

      {/* Preview modal */}
      {preview && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4" onClick={() => setPreview(null)}>
          <div
            className="w-full max-w-sm rounded-2xl border border-[#e6e8e3] bg-white p-5 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-[15px] font-bold text-[#24372b]">{preview.title} — preview</h3>
            <p className="mt-1 text-[11px] text-[#879188]">{preview.urgencyReason}</p>
            <ul className="mt-3 flex flex-col divide-y divide-[#eff1ed]">
              {preview.products.map((p) => (
                <li key={p.name} className="flex items-center gap-2.5 py-2 text-[12px] text-[#39473d]">
                  <span>{p.emoji}</span>
                  <span className="flex-1">{p.name}</span>
                  <span className="text-[10px] text-[#9aa39b]">{p.urgency}</span>
                </li>
              ))}
            </ul>
            {preview.price !== null && (
              <p className="mt-3 text-[12px] text-[#5c6b62]">
                Suggested bundle price: <b>₹{preview.price}</b>
                {preview.discount !== null && <> · {preview.discount}% off</>}{" "}
                <em className="text-[#a9b1a9]">(illustrative)</em>
              </p>
            )}
            <p className="mt-2 text-[10px] text-[#a9b1a9]">
              This is a local demo preview. No bundle promotion has been created or published.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <GhostButton onClick={() => setPreview(null)}>Close</GhostButton>
            </div>
          </div>
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
