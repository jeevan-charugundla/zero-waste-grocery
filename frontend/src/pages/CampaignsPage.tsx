import { useState } from "react";
import { Megaphone, Mail, MessageCircle, Eye, Plus, ShieldCheck } from "lucide-react";
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

type CampaignStatus = "draft" | "scheduled" | "paused";

interface Campaign {
  id: string;
  name: string;
  status: CampaignStatus;
  channel: "email" | "sms" | "push";
  audience: number;
  consentRate: string;
  optOuts: number;
  schedule: string;
  offer: string;
}

const seed: Campaign[] = [
  {
    id: "c1",
    name: "Milk markdown alert",
    status: "scheduled",
    channel: "email",
    audience: 412,
    consentRate: "94% opted in",
    optOuts: 3,
    schedule: "Tomorrow, 09:00",
    offer: "15% off whole milk 1L while stock lasts",
  },
  {
    id: "c2",
    name: "Breakfast bundle promo",
    status: "draft",
    channel: "push",
    audience: 587,
    consentRate: "81% opted in",
    optOuts: 11,
    schedule: "Not scheduled",
    offer: "Breakfast value pack at ₹149 (20% off)",
  },
  {
    id: "c3",
    name: "Weekend fresh picks",
    status: "paused",
    channel: "sms",
    audience: 236,
    consentRate: "89% opted in",
    optOuts: 5,
    schedule: "Paused — reschedule to publish",
    offer: "Fruit duo at ₹129 before the weekend",
  },
];

const channelLabels = { email: "Email", sms: "SMS", push: "Push" } as const;

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>(seed);
  const [preview, setPreview] = useState<Campaign | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const flash = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2600);
  };

  const totalAudience = campaigns.reduce((s, c) => s + c.audience, 0);
  const scheduled = campaigns.filter((c) => c.status === "scheduled").length;

  const schedule = (id: string) => {
    setCampaigns((cs) =>
      cs.map((c) => (c.id === id ? { ...c, status: "scheduled", schedule: "Tomorrow, 09:00 (local demo)" } : c))
    );
    flash("Demo action: campaign scheduled in local state only. No message will be sent; no real customers will be contacted.");
  };

  return (
    <>
      <PageHeader
        eyebrow="DEMO WORKSPACE"
        title="Customer campaigns"
        subtitle="Prepare consent-aware promotions for at-risk stock. Campaign scheduling here is a local demo interaction — no messages are sent and no real customers are contacted."
        action={<DemoBadge />}
      />

      <div className="mb-5 grid gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Campaigns" value={String(campaigns.length)} note={`${scheduled} scheduled (demo)`} icon={<Megaphone size={15} />} />
        <KpiCard label="Total audience" value={String(totalAudience)} note="consented profiles, demo data" icon={<ShieldCheck size={15} />} />
        <KpiCard label="Avg consent rate" value="88%" change="Across channels" changeTone="green" note="opt-in coverage" icon={<ShieldCheck size={15} />} />
        <KpiCard label="Opt-outs (last 7d)" value="19" change="Respect at all times" changeTone="neutral" note="excluded from sends" icon={<ShieldCheck size={15} />} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
        {/* List */}
        <div className="flex flex-col gap-3.5">
          {campaigns.length === 0 ? (
            <EmptyState icon={<Megaphone size={20} />} title="No campaigns yet" />
          ) : (
            campaigns.map((c) => (
              <Panel key={c.id}>
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <strong className="text-[13px] text-[#39473d]">{c.name}</strong>
                      <StatusBadge status={c.status} />
                      <Badge tone="outline">
                        {c.channel === "email" ? <Mail size={10} /> : c.channel === "sms" ? <MessageCircle size={10} /> : <Megaphone size={10} />} {channelLabels[c.channel]}
                      </Badge>
                    </div>
                    <p className="mt-1.5 text-[11px] text-[#8c978e]">Offer: {c.offer}</p>
                    <p className="mt-1 text-[11px] text-[#8c978e]">Schedule: {c.schedule}</p>
                    <p className="mt-2 text-[10.5px] text-[#9aa39b]">
                      Audience: <b className="text-[#5c6b62]">{c.audience}</b> ·{" "}
                      <span className="text-green-700">{c.consentRate}</span> ·{" "}
                      <span className="text-amber-700">{c.optOuts} opt-outs excluded</span>
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-wrap items-center gap-2">
                    <GhostButton onClick={() => setPreview(c)}>
                      <Eye size={12} /> Preview
                    </GhostButton>
                    {c.status === "draft" && (
                      <PrimaryButton onClick={() => schedule(c.id)} className="py-1.5">
                        Schedule (demo)
                      </PrimaryButton>
                    )}
                  </div>
                </div>
              </Panel>
            ))
          )}
          <Panel className="border-dashed">
            <div className="flex flex-col items-center gap-2 py-4 text-center">
              <Plus size={18} className="text-[#8a958d]" />
              <p className="text-[11px] text-[#8a958d]">
                Campaign creation is available in the backend workflow — this frontend keeps it in demo mode for now.
              </p>
            </div>
          </Panel>
        </div>

        {/* Side panel */}
        <Panel title="Consent & privacy" subtitle="How demo campaigns respect customer choice">
          <ul className="flex flex-col gap-2.5 text-[11px] leading-relaxed text-[#5c6b62]">
            <li className="flex gap-2">
              <ShieldCheck size={13} className="mt-0.5 shrink-0 text-green-700" />
              Only customers with recorded marketing opt-in are counted in audiences.
            </li>
            <li className="flex gap-2">
              <ShieldCheck size={13} className="mt-0.5 shrink-0 text-green-700" />
              Opt-outs (19 in the last 7 days) are excluded from every send.
            </li>
            <li className="flex gap-2">
              <ShieldCheck size={13} className="mt-0.5 shrink-0 text-green-700" />
              Nothing sends while in demo mode — scheduling updates local state only.
            </li>
          </ul>
        </Panel>
      </div>

      {/* Preview modal */}
      {preview && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4" onClick={() => setPreview(null)}>
          <div className="w-full max-w-sm rounded-2xl border border-[#e6e8e3] bg-white p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-[15px] font-bold text-[#24372b]">{preview.name} — preview</h3>
            <p className="mt-1 text-[11px] text-[#879188]">Channel: {channelLabels[preview.channel]}</p>
            <div className="mt-3 rounded-xl border border-[#eef0ec] bg-[#f8f9f6] p-3.5">
              <p className="text-[12px] font-semibold text-[#39473d]">Freshwise · {preview.name}</p>
              <p className="mt-1.5 text-[12px] text-[#5c6b62]">{preview.offer}</p>
              <p className="mt-2 text-[10px] text-[#9aa39b]">
                Demo content only. Draft copy — not reviewed, not delivered.
              </p>
            </div>
            <p className="mt-2 text-[10px] text-[#a9b1a9]">
              This message has not been sent to anyone. Preview is illustrative.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <GhostButton onClick={() => setPreview(null)}>Close</GhostButton>
            </div>
          </div>
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

function StatusBadge({ status }: { status: CampaignStatus }) {
  const tone: BadgeTone =
    status === "scheduled" ? "green" : status === "paused" ? "amber" : "neutral";
  const label = status === "scheduled" ? "Scheduled (demo)" : status === "paused" ? "Paused" : "Draft";
  return <Badge tone={tone}>{label}</Badge>;
}
