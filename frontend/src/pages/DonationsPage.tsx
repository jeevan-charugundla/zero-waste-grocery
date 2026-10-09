import { useState } from "react";
import { Heart, Trash2, AlertTriangle, ShieldAlert, Clock } from "lucide-react";
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

type Safety = "eligible" | "review" | "unsafe";

interface Item {
  id: string;
  product: string;
  batch: string;
  expiry: string;
  qty: number;
  unit: string;
  safety: Safety;
  route: string;
  warning?: string;
}

const seed: Item[] = [
  {
    id: "d1",
    product: "Whole Wheat Bread",
    batch: "BR-552",
    expiry: "4 days remaining",
    qty: 24,
    unit: "loaves",
    safety: "eligible",
    route: "Suggested: community kitchen pickup (same day)",
  },
  {
    id: "d2",
    product: "Apples (loose)",
    batch: "AP-118",
    expiry: "3 days remaining",
    qty: 18,
    unit: "kg",
    safety: "eligible",
    route: "Suggested: food bank drop-off, cold chain not required",
  },
  {
    id: "d3",
    product: "Fresh Strawberries",
    batch: "S-221",
    expiry: "2 days remaining",
    qty: 14,
    unit: "packs",
    safety: "review",
    route: "Suggested: Same-day donation or discharge to disposal if not collected today.",
    warning: "Cold-chain sensitive — verify temperature log before donating.",
  },
  {
    id: "d4",
    product: "Whole Milk 1L",
    batch: "M-098",
    expiry: "Expired yesterday",
    qty: 6,
    unit: "units",
    safety: "unsafe",
    route: "Suggested: safe disposal — do not donate.",
    warning: "Expired product. Never present as edible donation.",
  },
  {
    id: "d5",
    product: "Chilled Chicken Salad",
    batch: "CS-004",
    expiry: "Expired 2 days ago",
    qty: 4,
    unit: "packs",
    safety: "unsafe",
    route: "Suggested: certified hazardous waste disposal path.",
      warning: "Expired ready-to-eat item. Never present as edible donation.",
  },
];

const safetyMeta: Record<Safety, { tone: "green" | "amber" | "red"; label: string }> = {
  eligible: { tone: "green", label: "Donation eligible" },
  review: { tone: "amber", label: "Safety review required" },
  unsafe: { tone: "red", label: "Not donation-safe" },
};

export default function DonationsPage() {
  const [items, setItems] = useState<Item[]>(seed);
  const [toast, setToast] = useState<string | null>(null);

  const flash = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2600);
  };

  const complete = (id: string, kind: "donated" | "disposed" | "reviewed") => {
    setItems((list) => list.filter((i) => i.id !== id));
    flash(
      kind === "donated"
        ? "Demo action: marked as donated in local state only. No real donation record was created and no goods were moved."
        : kind === "disposed"
          ? "Demo action: marked as disposed in local state only. No real disposal action was executed."
          : "Demo action: safety review acknowledged in local state only."
    );
  };

  const eligible = seed.filter((i) => i.safety === "eligible").length;
  const review = seed.filter((i) => i.safety === "review").length;
  const unsafe = seed.filter((i) => i.safety === "unsafe").length;
  const unsafeUnits = seed.filter((i) => i.safety === "unsafe").reduce((s, i) => s + i.qty, 0);

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="Donations & disposal"
        subtitle="Route surplus safely: donate what's edible, dispose of what isn't. Safety states are clearly labelled; actions below only change local demo state and never move real product."
        action={<DemoBadge />}
      />

      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Donation eligible" value={String(eligible)} note="batches ready to route" icon={<Heart size={15} />} />
        <KpiCard label="Safety review" value={String(review)} change="Verify first" changeTone="amber" note="before donating" icon={<AlertTriangle size={15} />} />
        <KpiCard label="Not donation-safe" value={String(unsafe)} changeTone="red" note="require disposal" icon={<ShieldAlert size={15} />} />
        <KpiCard label="Units to dispose" value={String(unsafeUnits)} changeTone="red" note="never donate expired stock" icon={<Trash2 size={15} />} />
      </div>

      {/* Critical warning */}
      <div className="mb-5 flex items-start gap-3 rounded-xl border-[1.5px] border-[#f2d8d0] bg-[#fdf1ee] px-4 py-3.5">
        <ShieldAlert size={18} className="mt-0.5 shrink-0 text-[#b45e48]" />
        <div>
          <strong className="block text-[12px] font-bold text-[#8f4a37]">
            Never present expired or unsafe products as edible donations
          </strong>
          <p className="mt-0.5 text-[11px] text-[#a87367]">
            {unsafe} batch group(s) in this workspace are expired or unsafe. They must follow the
            disposal path — not the donation path.
          </p>
        </div>
      </div>

      {/* Items */}
      {items.length === 0 ? (
        <EmptyState icon={<Heart size={20} />} title="All items actioned" description="Local demo list is empty." />
      ) : (
        <div className="flex flex-col gap-3.5">
          {items.map((i) => (
            <Panel
              key={i.id}
              className={i.safety === "unsafe" ? "border-[1.5px] border-[#f2d8d0] bg-[#fefafa]" : ""}
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <strong className="text-[13px] text-[#39473d]">{i.product}</strong>
                    <Badge tone={safetyMeta[i.safety].tone}>{safetyMeta[i.safety].label}</Badge>
                    <Badge tone="outline">Batch {i.batch}</Badge>
                    <span className="flex items-center gap-1 text-[10.5px] text-[#9aa39b]">
                      <Clock size={11} /> {i.expiry}
                    </span>
                  </div>
                  {i.warning && (
                    <p className="mt-2 flex items-center gap-1.5 text-[11px] font-semibold text-[#b45e48]">
                      <AlertTriangle size={12} className="shrink-0" />
                      {i.warning}
                    </p>
                  )}
                  <p className="mt-1.5 text-[11px] text-[#8c978e]">{i.route}</p>
                  <p className="mt-1 text-[11px] text-[#9aa39b]">
                    Available quantity: <b className="text-[#5c6b62]">{i.qty} {i.unit}</b>
                  </p>
                </div>
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  {i.safety === "eligible" && (
                    <PrimaryButton onClick={() => complete(i.id, "donated")} className="py-1.5">
                      <Heart size={13} /> Mark donated (demo)
                    </PrimaryButton>
                  )}
                  {i.safety === "review" && (
                    <>
                      <PrimaryButton onClick={() => complete(i.id, "reviewed")} className="py-1.5">
                        Mark reviewed (demo)
                      </PrimaryButton>
                      <GhostButton onClick={() => complete(i.id, "disposed")}>
                        <Trash2 size={12} /> Dispose (demo)
                      </GhostButton>
                    </>
                  )}
                  {i.safety === "unsafe" && (
                    <PrimaryButton
                      onClick={() => complete(i.id, "disposed")}
                      className="py-1.5 bg-[#b45e48] hover:bg-[#8f4a37]"
                    >
                      <Trash2 size={13} /> Dispose only (demo)
                    </PrimaryButton>
                  )}
                </div>
              </div>
            </Panel>
          ))}
        </div>
      )}

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
