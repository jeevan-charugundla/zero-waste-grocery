import { useState, useMemo } from "react";
import {
  TrendingUp,
  Snowflake,
  RotateCw,
  Percent,
  Truck,
  Heart,
  Check,
  X,
  FileText,
  Edit3,
  Bot,
  AlertTriangle,
  Sparkles,
} from "lucide-react";

interface AgentStatus {
  id: string;
  name: string;
  icon: typeof TrendingUp;
  description: string;
  status: "Idle" | "Proposing" | "Simulating";
  proposalsCount: number;
  lastRun: string;
  color: string;
}

interface ProposalItem {
  id: string;
  action: "Propose donation" | "Dynamic markdown" | "Inter-store transfer" | "Flash bundle" | "Inventory reorder";
  productName: string;
  sku: string;
  storeFrom: string;
  destination?: string;
  quantity: number;
  wasteAvoided: number;
  financialImpact: number;
  confidence: number;
  status: "open" | "approved" | "rejected";
  batchCode: string;
  timing: string;
  sourceAgent: string;
  createdTime: string;
  rationale: string;
  constraints: string[];
}

const INITIAL_AGENTS: AgentStatus[] = [
  {
    id: "demand",
    name: "Demand Agent",
    icon: TrendingUp,
    description: "Forecasts per-store daily demand over the...",
    status: "Idle",
    proposalsCount: 3,
    lastRun: "09:28 pm",
    color: "#10b981",
  },
  {
    id: "freshness",
    name: "Freshness Agent",
    icon: Snowflake,
    description: "Scores batch spoilage risk from shelf life & sel...",
    status: "Idle",
    proposalsCount: 9,
    lastRun: "09:19 pm",
    color: "#06b6d4",
  },
  {
    id: "replenishment",
    name: "Replenishment Agent",
    icon: RotateCw,
    description: "Adjusts inbound orders vs. safety stock",
    status: "Idle",
    proposalsCount: 12,
    lastRun: "09:19 pm",
    color: "#3b82f6",
  },
  {
    id: "markdown",
    name: "Markdown Agent",
    icon: Percent,
    description: "Proposes discounts within markdown limits",
    status: "Idle",
    proposalsCount: 9,
    lastRun: "09:18 pm",
    color: "#8b5cf6",
  },
  {
    id: "transfer",
    name: "Transfer Agent",
    icon: Truck,
    description: "Matches surplus to shortages across...",
    status: "Idle",
    proposalsCount: 9,
    lastRun: "09:17 pm",
    color: "#f59e0b",
  },
  {
    id: "rescue",
    name: "Food Rescue Agent",
    icon: Heart,
    description: "Checks donation eligibility & partner...",
    status: "Idle",
    proposalsCount: 9,
    lastRun: "09:17 pm",
    color: "#ec4899",
  },
];

const INITIAL_PROPOSALS: ProposalItem[] = [
  {
    id: "R-105",
    action: "Propose donation",
    productName: "Spinach Bunch",
    sku: "VEG - SPN - BN",
    storeFrom: "Central Market",
    destination: "Community Food Hub",
    quantity: 47,
    wasteAvoided: 47,
    financialImpact: 0,
    confidence: 86,
    status: "approved",
    batchCode: "B-SPNA01",
    timing: "Today, Before 2 PM",
    sourceAgent: "Rescue",
    createdTime: "07:25 AM",
    rationale:
      "Without action today, about 23 of 70 units sell before expiry, leaving 47 units destined for disposal. Donating secures immediate rescue and eliminates spoilage loss.",
    constraints: [
      "Partner pickup must occur on schedule",
      "Cold chain verified (2°C – 4°C sustained)",
      "Food safety verified (inspection cleared)",
    ],
  },
  {
    id: "R-104",
    action: "Dynamic markdown",
    productName: "Strawberries 250g",
    sku: "FRU - STR - 250",
    storeFrom: "Whitefield Hub",
    destination: "Consumer Flash Sale",
    quantity: 24,
    wasteAvoided: 24,
    financialImpact: 1240,
    confidence: 92,
    status: "open",
    batchCode: "B-STRW04",
    timing: "Today, 12:00 PM – 08:00 PM",
    sourceAgent: "Markdown",
    createdTime: "08:10 AM",
    rationale:
      "Berry quality is optimal but shelf-life ends in 36 hours. A 35% discount accelerates velocity and recovers ₹1,240 gross margin before spoilage occurs.",
    constraints: [
      "Must not violate store category minimum price rule",
      "Limit to 2 units per customer basket",
    ],
  },
  {
    id: "R-103",
    action: "Inter-store transfer",
    productName: "Greek Yogurt 500g",
    sku: "DAI - YOG - 500",
    storeFrom: "Central Market",
    destination: "Indiranagar Branch",
    quantity: 30,
    wasteAvoided: 30,
    financialImpact: 2100,
    confidence: 88,
    status: "open",
    batchCode: "B-YOG09",
    timing: "Today, 01:30 PM Route",
    sourceAgent: "Transfer",
    createdTime: "08:45 AM",
    rationale:
      "Central Market has 5 days of overstock while Indiranagar has stockout risk on Greek Yogurt. Transferring 30 units matches unmet demand and prevents markdown erosion.",
    constraints: [
      "Refrigerated van temperature logging required",
      "Transfer distance within 12 km delivery radius",
    ],
  },
  {
    id: "R-102",
    action: "Flash bundle",
    productName: "Whole Wheat Bread 400g",
    sku: "BAK - BRD - WW",
    storeFrom: "Koramangala",
    destination: "Breakfast Bundle Shelf",
    quantity: 18,
    wasteAvoided: 18,
    financialImpact: 860,
    confidence: 94,
    status: "open",
    batchCode: "B-BRD12",
    timing: "Today, Afternoon Rush",
    sourceAgent: "Demand",
    createdTime: "09:05 AM",
    rationale:
      "Bakery items have 24-hour remaining shelf life. Bundling with organic peanut butter stimulates afternoon velocity with 94% sell-through probability.",
    constraints: [
      "Display near checkout aisle 2",
      "Sticker package with clear Same-Day consumption notice",
    ],
  },
  {
    id: "R-101",
    action: "Propose donation",
    productName: "Whole Milk 1L",
    sku: "DAI - MLK - 1L",
    storeFrom: "Indiranagar",
    destination: "Akshaya Shelter",
    quantity: 20,
    wasteAvoided: 20,
    financialImpact: 0,
    confidence: 91,
    status: "approved",
    batchCode: "B-MLK07",
    timing: "Today, Before 11:30 AM",
    sourceAgent: "Rescue",
    createdTime: "06:50 AM",
    rationale:
      "Unsold pasteurized dairy within 18 hours of expiry. Verified partner Akshaya has immediate breakfast utilization for 60 children.",
    constraints: [
      "Seals intact and temperature below 4°C",
      "Digital receipt signed upon driver handover",
    ],
  },
];

export default function DecisionRoomPage({
  searchQuery = "",
}: {
  searchQuery?: string;
}) {
  const [proposals, setProposals] = useState<ProposalItem[]>(INITIAL_PROPOSALS);
  const [activeTab, setActiveTab] = useState<"open" | "approved" | "rejected">("approved");
  const [selectedId, setSelectedId] = useState<string>("R-105");
  const [showRationaleModal, setShowRationaleModal] = useState<boolean>(false);
  const [simulating, setSimulating] = useState<boolean>(false);

  // Filter proposals by active tab and search query
  const filteredProposals = useMemo(() => {
    return proposals.filter((p) => {
      const matchesTab = p.status === activeTab;
      const matchesSearch =
        !searchQuery ||
        p.productName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesTab && matchesSearch;
    });
  }, [proposals, activeTab, searchQuery]);

  // Active selected item
  const selectedProposal = useMemo(() => {
    return proposals.find((p) => p.id === selectedId) || proposals[0];
  }, [proposals, selectedId]);

  // Approve action
  const handleApprove = (id: string) => {
    setProposals((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status: "approved" } : p))
    );
  };

  // Reject action
  const handleReject = (id: string) => {
    setProposals((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status: "rejected" } : p))
    );
  };

  // Simulate agent reasoning pulse
  const triggerSimulation = () => {
    setSimulating(true);
    setTimeout(() => {
      setSimulating(false);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      {/* ── Page Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#16271e] sm:text-3xl">
            AI Decision Room
          </h1>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-[#5e7165]">
            Agents propose, the coordinator selects a feasible plan, and you decide. Agent activity is simulated with deterministic rules — no live AI models are connected.
          </p>
        </div>

        <button
          onClick={triggerSimulation}
          className={`inline-flex shrink-0 items-center gap-2 rounded-full border border-[#92ddb8] bg-[#f0fbf5] px-4 py-2 text-xs font-semibold text-[#186441] shadow-sm transition hover:bg-[#e2f7ed] ${
            simulating ? "animate-pulse" : ""
          }`}
        >
          <Bot size={15} className="text-[#10b981]" />
          <span>{simulating ? "SIMULATING AGENTS…" : "SIMULATED AGENTS"}</span>
        </button>
      </div>

      {/* ── Row of 6 Agent Cards ── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {INITIAL_AGENTS.map((agent) => {
          const Icon = agent.icon;
          return (
            <div
              key={agent.id}
              className="flex flex-col justify-between rounded-2xl border border-[#e5ebe5] bg-white p-3.5 shadow-[0_2px_8px_rgba(0,0,0,0.02)] transition hover:shadow-md"
            >
              <div>
                <div className="flex items-center justify-between">
                  <div
                    className="grid h-8 w-8 place-items-center rounded-xl"
                    style={{ backgroundColor: `${agent.color}18` }}
                  >
                    <Icon size={16} style={{ color: agent.color }} />
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#4b6152]">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#10b981]" />
                    <span>{agent.status}</span>
                  </div>
                </div>

                <h3 className="mt-2.5 text-xs font-bold text-[#1e2f24]">{agent.name}</h3>
                <p className="mt-1 text-[11px] leading-snug text-[#738578] line-clamp-2">
                  {agent.description}
                </p>
              </div>

              <div className="mt-3.5 flex items-center justify-between border-t border-[#f0f4ef] pt-2 text-[10.5px] text-[#6b7d70]">
                <span className="font-semibold text-[#25392c]">
                  {agent.proposalsCount} proposals
                </span>
                <span className="text-[#8e9f93]">{agent.lastRun}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Main Two-Column Decision Board ── */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Column: Recommendation feed */}
        <div className="lg:col-span-5 flex flex-col space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold tracking-tight text-[#1e2f24]">
              Recommendation feed
            </h2>

            {/* Filter pills */}
            <div className="inline-flex rounded-full border border-[#dce3dc] bg-[#f5f8f5] p-0.5 text-xs font-medium">
              <button
                onClick={() => setActiveTab("open")}
                className={`rounded-full px-3 py-1 transition ${
                  activeTab === "open"
                    ? "bg-[#186441] text-white shadow-sm"
                    : "text-[#5e7165] hover:text-[#186441]"
                }`}
              >
                Open
              </button>
              <button
                onClick={() => setActiveTab("approved")}
                className={`rounded-full px-3 py-1 transition ${
                  activeTab === "approved"
                    ? "bg-[#186441] text-white shadow-sm"
                    : "text-[#5e7165] hover:text-[#186441]"
                }`}
              >
                Approved
              </button>
              <button
                onClick={() => setActiveTab("rejected")}
                className={`rounded-full px-3 py-1 transition ${
                  activeTab === "rejected"
                    ? "bg-[#186441] text-white shadow-sm"
                    : "text-[#5e7165] hover:text-[#186441]"
                }`}
              >
                Rejected
              </button>
            </div>
          </div>

          {/* Cards feed */}
          <div className="space-y-2.5">
            {filteredProposals.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[#d8e0d8] bg-white p-8 text-center text-xs text-[#738578]">
                No proposals in this view.
              </div>
            ) : (
              filteredProposals.map((item) => {
                const isSelected = item.id === selectedId;
                const isApproved = item.status === "approved";
                const isRejected = item.status === "rejected";

                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedId(item.id)}
                    className={`cursor-pointer rounded-2xl border p-4 transition ${
                      isSelected
                        ? "border-[#6dd6a5] bg-[#edf8f2] shadow-[0_4px_14px_rgba(24,100,65,0.08)] ring-1 ring-[#6dd6a5]"
                        : "border-[#e2e8e2] bg-white hover:border-[#b4d6c1] hover:bg-[#fbfdfb]"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-[#4e6456]">{item.id}</span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide ${
                          isApproved
                            ? "bg-[#d4f2e1] text-[#14603d]"
                            : isRejected
                            ? "bg-[#fae2df] text-[#a83428]"
                            : "bg-[#eaf0ea] text-[#364d3f]"
                        }`}
                      >
                        {item.status === "approved" ? "Approved" : item.status === "rejected" ? "Rejected" : "Open"}
                      </span>
                    </div>

                    <div className="mt-2 flex items-center gap-2">
                      <Heart size={15} className="text-[#10b981]" />
                      <h4 className="text-sm font-bold text-[#192b20]">
                        {item.action}
                      </h4>
                    </div>

                    <p className="mt-1 text-xs text-[#526658]">
                      {item.productName} · Store A · {item.quantity}u
                    </p>

                    <div className="mt-3 flex items-center gap-2 text-[11px] font-medium text-[#4a6152]">
                      <span className="rounded-md bg-[#e3eae3] px-2 py-0.5">
                        +₹{item.financialImpact}
                      </span>
                      <span className="rounded-md bg-[#e3eae3] px-2 py-0.5">
                        -{item.wasteAvoided}u waste
                      </span>
                      <span className="ml-auto text-[#627768]">
                        {item.confidence}% conf.
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Detailed Recommendation Inspector */}
        <div className="lg:col-span-7">
          {selectedProposal ? (
            <div className="rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-[0_4px_20px_rgba(0,0,0,0.03)]">
              {/* Header tags */}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs">
                  <span className="font-mono font-semibold text-[#526658]">
                    {selectedProposal.id}
                  </span>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                      selectedProposal.status === "approved"
                        ? "bg-[#d4f2e1] text-[#14603d]"
                        : selectedProposal.status === "rejected"
                        ? "bg-[#fae2df] text-[#a83428]"
                        : "bg-[#eaf0ea] text-[#364d3f]"
                    }`}
                  >
                    {selectedProposal.status === "approved"
                      ? "Approved"
                      : selectedProposal.status === "rejected"
                      ? "Rejected"
                      : "Pending Decision"}
                  </span>
                </div>

                {/* Top Action Buttons */}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => setShowRationaleModal((prev) => !prev)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-[#d8e0d8] bg-white px-3 py-1.5 text-xs font-semibold text-[#273d2f] hover:bg-[#f6f9f6]"
                  >
                    <FileText size={13} className="text-[#5e7165]" />
                    <span>View rationale</span>
                  </button>
                  <button
                    onClick={() => alert("Edit parameters modal (simulated in demo)")}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-[#d8e0d8] bg-white px-3 py-1.5 text-xs font-semibold text-[#273d2f] hover:bg-[#f6f9f6]"
                  >
                    <Edit3 size={13} className="text-[#5e7165]" />
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={() => handleReject(selectedProposal.id)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-[#e8d2d0] bg-[#fff8f7] px-3.5 py-1.5 text-xs font-semibold text-[#a83428] hover:bg-[#fdebea]"
                  >
                    <X size={13} />
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleApprove(selectedProposal.id)}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-[#28a76e] px-4 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-[#208f5d]"
                  >
                    <Check size={14} />
                    <span>Approve</span>
                  </button>
                </div>
              </div>

              {/* Title & subtitle */}
              <div className="mt-4 border-b border-[#edf2ec] pb-4">
                <h2 className="text-xl font-bold tracking-tight text-[#16271e]">
                  {selectedProposal.action}
                </h2>
                <p className="mt-1 text-xs text-[#526658]">
                  {selectedProposal.productName} ({selectedProposal.sku}) · {selectedProposal.storeFrom} ➔ {selectedProposal.destination || "Beneficiary"}
                </p>
              </div>

              {showRationaleModal && (
                <div className="mt-3 rounded-2xl bg-[#edf8f2] border border-[#6dd6a5] p-4 text-xs text-[#16432e]">
                  <div className="flex items-center justify-between font-bold">
                    <span className="flex items-center gap-1.5">
                      <Sparkles size={14} className="text-[#10b981]" />
                      Coordinator Rationale Insight
                    </span>
                    <button
                      onClick={() => setShowRationaleModal(false)}
                      className="text-[#557866] hover:text-[#16432e]"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <p className="mt-2 leading-relaxed">
                    {selectedProposal.rationale}
                  </p>
                </div>
              )}

              {/* 8 Metric Boxes Grid (4 columns x 2 rows) */}
              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Quantity</span>
                  <strong className="mt-1 block text-sm font-bold text-[#1b2d22]">
                    {selectedProposal.quantity} Units
                  </strong>
                </div>

                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Timing</span>
                  <strong className="mt-1 block text-sm font-bold text-[#1b2d22] truncate">
                    {selectedProposal.timing}
                  </strong>
                </div>

                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Confidence (sim.)</span>
                  <strong className="mt-1 block text-sm font-bold text-[#1b2d22]">
                    {selectedProposal.confidence}%
                  </strong>
                </div>

                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Financial impact</span>
                  <strong className="mt-1 block text-sm font-bold text-[#1b2d22]">
                    +₹{selectedProposal.financialImpact}
                  </strong>
                </div>

                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Waste avoided</span>
                  <strong className="mt-1 block text-sm font-bold text-[#1b2d22]">
                    {selectedProposal.wasteAvoided} Units
                  </strong>
                </div>

                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Batch</span>
                  <strong className="mt-1 block text-sm font-mono font-bold text-[#1b2d22]">
                    {selectedProposal.batchCode}
                  </strong>
                </div>

                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Source agent</span>
                  <strong className="mt-1 block text-sm font-bold text-[#1b2d22]">
                    {selectedProposal.sourceAgent}
                  </strong>
                </div>

                <div className="rounded-2xl border border-[#e6ece6] bg-[#f7faf7] p-3">
                  <span className="block text-[10.5px] font-medium text-[#738779]">Created</span>
                  <strong className="mt-1 block text-sm font-bold text-[#1b2d22]">
                    {selectedProposal.createdTime}
                  </strong>
                </div>
              </div>

              {/* Rationale & Constraints */}
              <div className="mt-5 space-y-4">
                <div className="rounded-2xl border border-[#e4ebe4] bg-white p-4">
                  <h4 className="flex items-center gap-1.5 text-xs font-bold text-[#23382b]">
                    <Sparkles size={14} className="text-[#10b981]" />
                    <span>Agent Rationale</span>
                  </h4>
                  <p className="mt-2 text-xs leading-relaxed text-[#516457]">
                    {selectedProposal.rationale}
                  </p>
                </div>

                <div className="rounded-2xl border border-[#e4ebe4] bg-white p-4">
                  <h4 className="flex items-center gap-1.5 text-xs font-bold text-[#23382b]">
                    <AlertTriangle size={14} className="text-[#f59e0b]" />
                    <span>Constraints & risks</span>
                  </h4>
                  <ul className="mt-2 space-y-1.5 text-xs text-[#516457]">
                    {selectedProposal.constraints.map((c, idx) => (
                      <li key={idx} className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#f59e0b]" />
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-3xl border border-[#dfe5df] bg-white p-12 text-center text-sm text-[#738578]">
              Select a proposal from the feed to inspect details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
