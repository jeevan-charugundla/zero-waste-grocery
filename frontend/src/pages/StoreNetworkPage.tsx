import { useState, useMemo } from "react";
import {
  Bot,
  Truck,
  CheckCircle2,
  History,
  Search,
  AlertTriangle,
  Download,
  Check,
  ShieldCheck,
  Info,
} from "lucide-react";

interface StoreNode {
  id: string;
  name: string;
  code: string;
  health: number;
  highRiskSkus: number;
  surplusUnits: number;
  shortUnits: number;
  valuation: number;
  borderColor: "green" | "amber";
  x: number;
  y: number;
}

export interface ProposedTransfer {
  id: string;
  product: string;
  batchCode: string;
  route: string; // e.g. "C → B" or "A → B"
  fromStoreCode: string;
  toStoreCode: string;
  fromStoreName: string;
  toStoreName: string;
  qty: number;
  transportCost: number;
  travelHours: string;
  shelfAtArrival: string;
  isFeasible: boolean;
  feasibilityReason?: string;
  distanceKm: number;
  strategies: {
    noAction: { waste: number; financial: number; desc: string };
    markdown: { waste: number; financial: number; desc: string };
    transfer: { waste: number; financial: number; desc: string };
    reduceOrder: { waste: number; financial: number; desc: string };
  };
  summaryText: string;
}

export interface PastTransferHistory {
  id: string;
  transferNumber: string;
  product: string;
  batchCode: string;
  route: string;
  fromStore: string;
  toStore: string;
  qty: number;
  cost: number;
  dispatchedAt: string;
  deliveredAt: string;
  status: "Delivered" | "In Transit";
  wastePreventedUnits: number;
  wastePreventedKg: number;
  marginGain: number;
  driver: string;
  vehicle: string;
  coldChainVerified: boolean;
}

const STORE_NODES: StoreNode[] = [
  {
    id: "store_a",
    name: "Central Market",
    code: "Store A",
    health: 65,
    highRiskSkus: 5,
    surplusUnits: 369,
    shortUnits: 167,
    valuation: 46940,
    borderColor: "amber",
    x: 50,
    y: 20,
  },
  {
    id: "store_b",
    name: "Tech Park",
    code: "Store B",
    health: 100,
    highRiskSkus: 0,
    surplusUnits: 0,
    shortUnits: 568,
    valuation: 17870,
    borderColor: "green",
    x: 20,
    y: 80,
  },
  {
    id: "store_c",
    name: "Lakeview",
    code: "Store C",
    health: 66,
    highRiskSkus: 3,
    surplusUnits: 190,
    shortUnits: 190,
    valuation: 22875,
    borderColor: "amber",
    x: 80,
    y: 80,
  },
];

const PROPOSED_TRANSFERS: ProposedTransfer[] = [
  {
    id: "tr-01",
    product: "Toned Milk 1L",
    batchCode: "B-MLKC01",
    route: "C → B",
    fromStoreCode: "Store C",
    toStoreCode: "Store B",
    fromStoreName: "Lakeview",
    toStoreName: "Tech Park",
    qty: 46,
    transportCost: 138,
    travelHours: "1.6h",
    shelfAtArrival: "1.9d",
    isFeasible: true,
    distanceKm: 18,
    strategies: {
      noAction: {
        waste: 46,
        financial: -1312,
        desc: "Baseline: sell at current price, write off remainder.",
      },
      markdown: {
        waste: 0,
        financial: -506,
        desc: "30% off lifts demand ~75% (simulated elasticity).",
      },
      transfer: {
        waste: 0,
        financial: 1402,
        desc: "Move 46 units to Tech Park (1.6h, shortage 86).",
      },
      reduceOrder: {
        waste: 28,
        financial: -429,
        desc: "Postpones next inbound; relieves future surplus, limited effect on current batch.",
      },
    },
    summaryText:
      "A transfer reuses stock already paid for: it fills a 46-unit gap at the destination for ₹138 in transport, instead of discounting margin at source and ordering fresh stock at destination.",
  },
  {
    id: "tr-02",
    product: "Robusta Bananas (dozen)",
    batchCode: "B-BANC01",
    route: "C → B",
    fromStoreCode: "Store C",
    toStoreCode: "Store B",
    fromStoreName: "Lakeview",
    toStoreName: "Tech Park",
    qty: 34,
    transportCost: 102,
    travelHours: "1.6h",
    shelfAtArrival: "1.9d",
    isFeasible: true,
    distanceKm: 18,
    strategies: {
      noAction: {
        waste: 34,
        financial: -1088,
        desc: "Baseline: left at Lakeview, ripening accelerates over 48h.",
      },
      markdown: {
        waste: 5,
        financial: -420,
        desc: "25% quick-sale discount on fresh shelf.",
      },
      transfer: {
        waste: 0,
        financial: 1190,
        desc: "Move 34 bunches to Tech Park morning gym rush.",
      },
      reduceOrder: {
        waste: 20,
        financial: -340,
        desc: "Skip tomorrow vendor intake, modest shelf relief.",
      },
    },
    summaryText:
      "High velocity morning demand at Tech Park absorbs 34 banana bunches before over-ripening, saving ₹1,190 in net retail margin.",
  },
  {
    id: "tr-03",
    product: "Fresh Curd 400g",
    batchCode: "B-CRDC01",
    route: "C → B",
    fromStoreCode: "Store C",
    toStoreCode: "Store B",
    fromStoreName: "Lakeview",
    toStoreName: "Tech Park",
    qty: 15,
    transportCost: 45,
    travelHours: "1.6h",
    shelfAtArrival: "2.9d",
    isFeasible: true,
    distanceKm: 18,
    strategies: {
      noAction: {
        waste: 15,
        financial: -525,
        desc: "Baseline: risk expiry within 3 days at Lakeview.",
      },
      markdown: {
        waste: 2,
        financial: -180,
        desc: "20% promotional discount tag applied.",
      },
      transfer: {
        waste: 0,
        financial: 570,
        desc: "Move 15 units to Tech Park lunch dairy coolers.",
      },
      reduceOrder: {
        waste: 8,
        financial: -150,
        desc: "Postpone dairy crate delivery by 24h.",
      },
    },
    summaryText:
      "2.9 days shelf life allows effortless refrigerated transfer with ₹45 transit cost, fulfilling immediate cafeteria demand at Tech Park.",
  },
  {
    id: "tr-04",
    product: "Tomatoes 1kg",
    batchCode: "B-TOMC01",
    route: "C → B",
    fromStoreCode: "Store C",
    toStoreCode: "Store B",
    fromStoreName: "Lakeview",
    toStoreName: "Tech Park",
    qty: 14,
    transportCost: 42,
    travelHours: "1.6h",
    shelfAtArrival: "1.9d",
    isFeasible: true,
    distanceKm: 18,
    strategies: {
      noAction: {
        waste: 14,
        financial: -560,
        desc: "Baseline: ambient heat causes softening.",
      },
      markdown: {
        waste: 3,
        financial: -210,
        desc: "35% markdown sticker for walk-ins.",
      },
      transfer: {
        waste: 0,
        financial: 518,
        desc: "Move 14 crates to Tech Park meal-kit prep.",
      },
      reduceOrder: {
        waste: 7,
        financial: -180,
        desc: "Trim next morning mandi pickup by 15kg.",
      },
    },
    summaryText:
      "Transit takes 1.6h in insulated crates. Immediate uptake in Tech Park evening salad prep completely prevents spoilage.",
  },
  {
    id: "tr-05",
    product: "Paneer 200g",
    batchCode: "B-PNRC01",
    route: "C → B",
    fromStoreCode: "Store C",
    toStoreCode: "Store B",
    fromStoreName: "Lakeview",
    toStoreName: "Tech Park",
    qty: 8,
    transportCost: 24,
    travelHours: "1.6h",
    shelfAtArrival: "1.9d",
    isFeasible: true,
    distanceKm: 18,
    strategies: {
      noAction: {
        waste: 8,
        financial: -720,
        desc: "High cost dairy spoilage at Lakeview.",
      },
      markdown: {
        waste: 1,
        financial: -240,
        desc: "25% discount for local loyalty members.",
      },
      transfer: {
        waste: 0,
        financial: 696,
        desc: "Move 8 packs to Tech Park high-end gourmet section.",
      },
      reduceOrder: {
        waste: 4,
        financial: -200,
        desc: "Lower cooperative supplier allotment.",
      },
    },
    summaryText:
      "Premium dairy preservation: ₹24 delivery overhead preserves 100% of the ₹696 retail contribution margin at Tech Park.",
  },
  {
    id: "tr-06",
    product: "Robusta Bananas (dozen)",
    batchCode: "B-BANA01",
    route: "A → B",
    fromStoreCode: "Store A",
    toStoreCode: "Store B",
    fromStoreName: "Central Market",
    toStoreName: "Tech Park",
    qty: 6,
    transportCost: 18,
    travelHours: "1.2h",
    shelfAtArrival: "3.0d",
    isFeasible: true,
    distanceKm: 14,
    strategies: {
      noAction: {
        waste: 6,
        financial: -192,
        desc: "Low volume surplus at Central Market.",
      },
      markdown: {
        waste: 0,
        financial: -72,
        desc: "Small bundle bundle deal.",
      },
      transfer: {
        waste: 0,
        financial: 174,
        desc: "Consolidate into Tech Park outbound logistics.",
      },
      reduceOrder: {
        waste: 3,
        financial: -60,
        desc: "Negligible effect on standard bulk pallet orders.",
      },
    },
    summaryText:
      "3.0 days shelf life gives ample runway. Consolidating with morning scheduled van trip costs only ₹18 in marginal fuel.",
  },
  {
    id: "tr-07",
    product: "Papaya (each)",
    batchCode: "B-PAPA01",
    route: "A → B",
    fromStoreCode: "Store A",
    toStoreCode: "Store B",
    fromStoreName: "Central Market",
    toStoreName: "Tech Park",
    qty: 6,
    transportCost: 18,
    travelHours: "1.2h",
    shelfAtArrival: "1.9d",
    isFeasible: true,
    distanceKm: 14,
    strategies: {
      noAction: {
        waste: 6,
        financial: -270,
        desc: "Central Market surplus over current weekend quota.",
      },
      markdown: {
        waste: 1,
        financial: -105,
        desc: "Cut-fruit combo promotion at counter.",
      },
      transfer: {
        waste: 0,
        financial: 252,
        desc: "Move 6 units to Tech Park juice bar kiosk.",
      },
      reduceOrder: {
        waste: 3,
        financial: -90,
        desc: "Skip weekend farmer crate delivery.",
      },
    },
    summaryText:
      "Tech Park juice corner has an immediate deficit of 8 papayas. Transferring 6 solves this shortage within 1.2 hours.",
  },
  {
    id: "tr-08",
    product: "Toned Milk 1L",
    batchCode: "B-MLKA01",
    route: "A → B",
    fromStoreCode: "Store A",
    toStoreCode: "Store B",
    fromStoreName: "Central Market",
    toStoreName: "Tech Park",
    qty: 86,
    transportCost: 258,
    travelHours: "1.2h",
    shelfAtArrival: "0.9d",
    isFeasible: false,
    feasibilityReason: "Shelf life at arrival too low",
    distanceKm: 14,
    strategies: {
      noAction: {
        waste: 86,
        financial: -2451,
        desc: "High risk of total batch dump if not sold today.",
      },
      markdown: {
        waste: 12,
        financial: 1100,
        desc: "RECOMMENDED: Flash 40% discount at Central Market now.",
      },
      transfer: {
        waste: 40,
        financial: -380,
        desc: "HIGH RISK: 0.9d shelf life means milk spoils before sale.",
      },
      reduceOrder: {
        waste: 50,
        financial: -1200,
        desc: "Does not resolve current batch expiring in under 24h.",
      },
    },
    summaryText:
      "INSPECTION WARNING: With only 0.9 days remaining, transferring 86 units across 1.2h introduces severe spoilage risk. In-store flash markdown is safer.",
  },
  {
    id: "tr-09",
    product: "Spinach Bunch",
    batchCode: "B-SPNA01",
    route: "A → B",
    fromStoreCode: "Store A",
    toStoreCode: "Store B",
    fromStoreName: "Central Market",
    toStoreName: "Tech Park",
    qty: 47,
    transportCost: 141,
    travelHours: "1.2h",
    shelfAtArrival: "0.9d",
    isFeasible: false,
    feasibilityReason: "Shelf life at arrival too low",
    distanceKm: 14,
    strategies: {
      noAction: {
        waste: 47,
        financial: -1410,
        desc: "Wilts within 20 hours at ambient temperatures.",
      },
      markdown: {
        waste: 8,
        financial: 680,
        desc: "RECOMMENDED: Bundle with lentils for immediate clearance.",
      },
      transfer: {
        waste: 35,
        financial: -250,
        desc: "HIGH RISK: Fragile leafy green will wilt during transit.",
      },
      reduceOrder: {
        waste: 30,
        financial: -600,
        desc: "Cannot save today's harvested batch.",
      },
    },
    summaryText:
      "INSPECTION WARNING: Fragile leafy greens lose moisture rapidly. AI suggests local discount rather than inter-store vehicle transfer.",
  },
  {
    id: "tr-10",
    product: "Whole Wheat Bread",
    batchCode: "B-BRDA01",
    route: "A → B",
    fromStoreCode: "Store A",
    toStoreCode: "Store B",
    fromStoreName: "Central Market",
    toStoreName: "Tech Park",
    qty: 44,
    transportCost: 132,
    travelHours: "1.2h",
    shelfAtArrival: "0.9d",
    isFeasible: false,
    feasibilityReason: "Shelf life at arrival too low",
    distanceKm: 14,
    strategies: {
      noAction: {
        waste: 44,
        financial: -1320,
        desc: "Bakery batch expires tonight at midnight.",
      },
      markdown: {
        waste: 6,
        financial: 590,
        desc: "RECOMMENDED: 50% evening bakery clearance at Store A.",
      },
      transfer: {
        waste: 30,
        financial: -180,
        desc: "HIGH RISK: Destination customers reject near-dated loaves.",
      },
      reduceOrder: {
        waste: 25,
        financial: -500,
        desc: "Adjust tomorrow morning bakery manifest.",
      },
    },
    summaryText:
      "INSPECTION WARNING: Bakery items under 1 day shelf life face customer bounce back at destination. Prefer local markdown or charity donation.",
  },
];

const PAST_TRANSFER_HISTORY: PastTransferHistory[] = [
  {
    id: "hist-01",
    transferNumber: "TR-2026-8842",
    product: "Toned Milk 1L",
    batchCode: "B-MLKC98",
    route: "C → B",
    fromStore: "Lakeview (Store C)",
    toStore: "Tech Park (Store B)",
    qty: 40,
    cost: 120,
    dispatchedAt: "Today, 08:30 AM",
    deliveredAt: "Today, 10:05 AM",
    status: "Delivered",
    wastePreventedUnits: 40,
    wastePreventedKg: 40.0,
    marginGain: 1250,
    driver: "Ramesh Kumar",
    vehicle: "EV-Van #04 (Refrigerated)",
    coldChainVerified: true,
  },
  {
    id: "hist-02",
    transferNumber: "TR-2026-8839",
    product: "Whole Wheat Bread",
    batchCode: "B-BRDA95",
    route: "A → C",
    fromStore: "Central Market (Store A)",
    toStore: "Lakeview (Store C)",
    qty: 25,
    cost: 75,
    dispatchedAt: "Yesterday, 04:15 PM",
    deliveredAt: "Yesterday, 05:10 PM",
    status: "Delivered",
    wastePreventedUnits: 25,
    wastePreventedKg: 10.0,
    marginGain: 780,
    driver: "Sunil Murthy",
    vehicle: "EV-Van #02",
    coldChainVerified: true,
  },
  {
    id: "hist-03",
    transferNumber: "TR-2026-8835",
    product: "Paneer 200g",
    batchCode: "B-PNRC89",
    route: "C → B",
    fromStore: "Lakeview (Store C)",
    toStore: "Tech Park (Store B)",
    qty: 18,
    cost: 54,
    dispatchedAt: "Yesterday, 11:20 AM",
    deliveredAt: "Yesterday, 12:55 PM",
    status: "Delivered",
    wastePreventedUnits: 18,
    wastePreventedKg: 3.6,
    marginGain: 620,
    driver: "Ramesh Kumar",
    vehicle: "EV-Van #04 (Refrigerated)",
    coldChainVerified: true,
  },
  {
    id: "hist-04",
    transferNumber: "TR-2026-8828",
    product: "Robusta Bananas (dozen)",
    batchCode: "B-BANA84",
    route: "A → B",
    fromStore: "Central Market (Store A)",
    toStore: "Tech Park (Store B)",
    qty: 30,
    cost: 90,
    dispatchedAt: "08 Oct, 09:00 AM",
    deliveredAt: "08 Oct, 10:15 AM",
    status: "Delivered",
    wastePreventedUnits: 30,
    wastePreventedKg: 36.0,
    marginGain: 950,
    driver: "Vikram Singh",
    vehicle: "EV-Van #01",
    coldChainVerified: true,
  },
  {
    id: "hist-05",
    transferNumber: "TR-2026-8815",
    product: "Fresh Curd 400g",
    batchCode: "B-CRDC77",
    route: "C → B",
    fromStore: "Lakeview (Store C)",
    toStore: "Tech Park (Store B)",
    qty: 20,
    cost: 60,
    dispatchedAt: "07 Oct, 02:40 PM",
    deliveredAt: "07 Oct, 04:15 PM",
    status: "Delivered",
    wastePreventedUnits: 20,
    wastePreventedKg: 8.0,
    marginGain: 740,
    driver: "Sunil Murthy",
    vehicle: "EV-Van #02",
    coldChainVerified: true,
  },
];

export default function StoreNetworkPage() {
  const [selectedTransferId, setSelectedTransferId] = useState<string>("tr-01");
  const [selectedStrategyType, setSelectedStrategyType] = useState<
    "noAction" | "markdown" | "transfer" | "reduceOrder"
  >("transfer");
  const [selectedStoreId, setSelectedStoreId] = useState<string>("store_c");

  // Filter & Search States
  const [activeTab, setActiveTab] = useState<"proposals" | "history">("proposals");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [routeFilter, setRouteFilter] = useState<string>("ALL");
  const [feasibilityFilter, setFeasibilityFilter] = useState<"ALL" | "FEASIBLE" | "LOW_SHELF">("ALL");

  // Toast confirmation
  const [dispatchedToast, setDispatchedToast] = useState<string | null>(null);

  const currentTransfer = useMemo(() => {
    return (
      PROPOSED_TRANSFERS.find((t) => t.id === selectedTransferId) ||
      PROPOSED_TRANSFERS[0]
    );
  }, [selectedTransferId]);

  // Filtered proposals list
  const filteredProposals = useMemo(() => {
    return PROPOSED_TRANSFERS.filter((item) => {
      const matchesSearch =
        item.product.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.batchCode.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesRoute =
        routeFilter === "ALL" ||
        (routeFilter === "C_TO_B" && item.route === "C → B") ||
        (routeFilter === "A_TO_B" && item.route === "A → B");

      const matchesFeasibility =
        feasibilityFilter === "ALL" ||
        (feasibilityFilter === "FEASIBLE" && item.isFeasible) ||
        (feasibilityFilter === "LOW_SHELF" && !item.isFeasible);

      return matchesSearch && matchesRoute && matchesFeasibility;
    });
  }, [searchQuery, routeFilter, feasibilityFilter]);

  // Filtered history list
  const filteredHistory = useMemo(() => {
    return PAST_TRANSFER_HISTORY.filter((item) => {
      return (
        item.product.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.batchCode.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.transferNumber.toLowerCase().includes(searchQuery.toLowerCase())
      );
    });
  }, [searchQuery]);

  const handleDispatch = (item: ProposedTransfer) => {
    setDispatchedToast(
      `Dispatched: ${item.qty} units of ${item.product} along route ${item.route}!`
    );
    setTimeout(() => setDispatchedToast(null), 4000);
  };

  const handleDownloadManifest = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      "Product,Batch,Route,Qty,Transport Cost,Travel,Shelf At Arrival,Feasibility\n" +
      PROPOSED_TRANSFERS.map(
        (t) =>
          `"${t.product}","${t.batchCode}","${t.route}",${t.qty},"₹${t.transportCost}","${t.travelHours}","${t.shelfAtArrival}","${
            t.isFeasible ? "Feasible" : "Shelf life at arrival too low"
          }"`
      ).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `store_transfer_manifest_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-7 pb-12">
      {/* ── Page Header ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#16271e] sm:text-3xl">
            Store Network
          </h1>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-[#5e7165]">
            Three connected stores and their transfer routes. Transfers shown here are proposals only — nothing is executed.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadManifest}
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#d6e2d8] bg-white px-3.5 py-1.5 text-xs font-semibold text-[#2c4e3a] shadow-xs hover:bg-[#f6faf7] transition"
          >
            <Download size={13} className="text-[#10b981]" />
            <span>Export Manifest</span>
          </button>

          <div className="inline-flex items-center gap-2 rounded-full border border-[#92ddb8] bg-[#f0fbf5] px-4 py-1.5 text-xs font-semibold text-[#186441] shadow-sm">
            <Bot size={14} className="text-[#10b981]" />
            <span>SIMULATED NETWORK</span>
          </div>
        </div>
      </div>

      {/* ── Toast Alert Banner ── */}
      {dispatchedToast && (
        <div className="flex items-center justify-between rounded-2xl border border-[#86efac] bg-[#f0fdf4] p-3.5 text-xs font-semibold text-[#166534] shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-[#16a34a]" />
            <span>{dispatchedToast}</span>
          </div>
          <button
            onClick={() => setDispatchedToast(null)}
            className="text-[11px] font-bold text-[#15803d] underline hover:text-[#14532d]"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ── Product Switcher Bar ── */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="font-bold text-[#495e51] shrink-0">Quick Focus:</span>
        {PROPOSED_TRANSFERS.slice(0, 5).map((prod) => (
          <button
            key={prod.id}
            onClick={() => setSelectedTransferId(prod.id)}
            className={`rounded-full px-3.5 py-1 font-semibold transition shrink-0 ${
              selectedTransferId === prod.id
                ? "bg-[#186441] text-white shadow-sm"
                : "border border-[#dce3dc] bg-white text-[#526658] hover:bg-[#f6f9f6]"
            }`}
          >
            {prod.product} ({prod.route})
          </button>
        ))}
      </div>

      {/* ── Main Two-Column Layout (Network Graph + Comparison Panel) ── */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Column: Network Graph Panel */}
        <div className="lg:col-span-7 flex flex-col rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-[#1b2d22]">Network graph</h2>
              <p className="text-xs text-[#708476]">
                Line weight = proposed transfer volume · Click a store node or route
              </p>
            </div>
            <span className="rounded-md bg-[#f0fdf4] border border-[#bbf7d0] px-2 py-0.5 text-[10px] font-bold text-[#166534]">
              Active: {currentTransfer.route} ({currentTransfer.qty} units)
            </span>
          </div>

          {/* SVG & Node Diagram Canvas */}
          <div className="relative mt-6 flex-1 min-h-[460px] w-full rounded-2xl bg-[#fafcfa] border border-[#edf3ed] p-4 flex flex-col justify-between overflow-hidden">
            {/* SVG Connecting Lines */}
            <svg
              className="absolute inset-0 h-full w-full pointer-events-none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Route Store A <-> Store B */}
              <line
                x1="50%"
                y1="22%"
                x2="22%"
                y2="78%"
                stroke={currentTransfer.route === "A → B" ? "#10b981" : "#c9d6cb"}
                strokeWidth={currentTransfer.route === "A → B" ? "6" : "2"}
                strokeDasharray={currentTransfer.route === "A → B" ? "none" : "5,5"}
                strokeLinecap="round"
              />

              {/* Route Store A <-> Store C */}
              <line
                x1="50%"
                y1="22%"
                x2="78%"
                y2="78%"
                stroke="#c9d6cb"
                strokeWidth="2"
                strokeDasharray="5,5"
              />

              {/* Route Store C <-> Store B */}
              <line
                x1="22%"
                y1="78%"
                x2="78%"
                y2="78%"
                stroke={currentTransfer.route === "C → B" ? "#10b981" : "#c9d6cb"}
                strokeWidth={currentTransfer.route === "C → B" ? "8" : "3"}
                strokeLinecap="round"
              />
            </svg>

            {/* Route Distance / Weight Badges */}
            <div
              onClick={() => {
                const aToBItem = PROPOSED_TRANSFERS.find((t) => t.route === "A → B");
                if (aToBItem) setSelectedTransferId(aToBItem.id);
              }}
              className={`cursor-pointer absolute top-[48%] left-[26%] -translate-x-1/2 -translate-y-1/2 rounded-md px-2.5 py-1 text-[10px] font-bold transition shadow-xs ${
                currentTransfer.route === "A → B"
                  ? "bg-[#186441] text-white ring-2 ring-[#10b981]"
                  : "bg-white/95 border border-[#e0e8e0] text-[#667d70] hover:bg-[#f2f7f3]"
              }`}
            >
              Route A ➔ B · 14 km · 1.2h
            </div>

            <div className="absolute top-[48%] right-[26%] translate-x-1/2 -translate-y-1/2 rounded-md bg-white/95 border border-[#e0e8e0] px-2 py-0.5 text-[10px] font-semibold text-[#667d70] shadow-xs">
              Route A ➔ C · 9 km · 0.8h
            </div>

            <div
              onClick={() => {
                const cToBItem = PROPOSED_TRANSFERS.find((t) => t.route === "C → B");
                if (cToBItem) setSelectedTransferId(cToBItem.id);
              }}
              className={`cursor-pointer absolute bottom-[23%] left-[50%] -translate-x-1/2 translate-y-1/2 rounded-full px-3 py-1 text-[11px] font-bold shadow-sm z-10 flex items-center gap-1.5 transition ${
                currentTransfer.route === "C → B"
                  ? "bg-[#10b981] text-white ring-4 ring-[#10b981]/25"
                  : "bg-white border border-[#10b981] text-[#107049] hover:bg-[#eaf8f1]"
              }`}
            >
              <Truck size={12} className={currentTransfer.route === "C → B" ? "text-white" : "text-[#10b981]"} />
              <span>Route C ➔ B · 18 km · 1.6h · {currentTransfer.qty}u active</span>
            </div>

            {/* Top Node: Store A */}
            <div className="relative z-10 flex justify-center">
              {renderStoreCard(
                STORE_NODES[0],
                selectedStoreId === STORE_NODES[0].id,
                () => setSelectedStoreId(STORE_NODES[0].id)
              )}
            </div>

            {/* Bottom Row Nodes: Store B and Store C */}
            <div className="relative z-10 flex justify-between items-end pt-12">
              {renderStoreCard(
                STORE_NODES[1],
                selectedStoreId === STORE_NODES[1].id,
                () => setSelectedStoreId(STORE_NODES[1].id)
              )}
              {renderStoreCard(
                STORE_NODES[2],
                selectedStoreId === STORE_NODES[2].id,
                () => setSelectedStoreId(STORE_NODES[2].id)
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Transfer Comparison Panel */}
        <div className="lg:col-span-5 flex flex-col justify-between rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-[#1b2d22]">Transfer comparison</h2>
                <p className="mt-0.5 text-xs text-[#708476]">
                  {currentTransfer.product}: {currentTransfer.fromStoreName} ➔ {currentTransfer.toStoreName}
                </p>
              </div>
              <span className="font-mono text-xs font-semibold text-[#5a7062] bg-[#f4f7f4] px-2 py-0.5 rounded">
                {currentTransfer.batchCode}
              </span>
            </div>

            {/* Infeasible alert warning if shelf life is too low */}
            {!currentTransfer.isFeasible && (
              <div className="mt-3.5 flex items-start gap-2.5 rounded-xl border border-[#fecaca] bg-[#fef2f2] p-3 text-xs text-[#991b1b]">
                <AlertTriangle size={15} className="text-[#dc2626] shrink-0 mt-0.5" />
                <div>
                  <strong className="font-bold">Transfer Infeasible:</strong> {currentTransfer.feasibilityReason}.
                  Remaining shelf life ({currentTransfer.shelfAtArrival}) is less than transit + customer consumption window.
                </div>
              </div>
            )}

            {/* 4 Strategy Cards */}
            <div className="mt-4 space-y-2.5">
              {/* 1. No Action */}
              <div
                onClick={() => setSelectedStrategyType("noAction")}
                className={`cursor-pointer rounded-2xl border p-3.5 transition ${
                  selectedStrategyType === "noAction"
                    ? "border-[#a5b4a8] bg-[#f8faf8] ring-1 ring-[#a5b4a8]"
                    : "border-[#e5ece5] bg-white hover:bg-[#fafbfa]"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <strong className="block text-xs font-bold text-[#1a2d20]">
                      No Action
                    </strong>
                    <p className="mt-1 text-[11.5px] leading-snug text-[#607466]">
                      {currentTransfer.strategies.noAction.desc}
                    </p>
                  </div>
                  <div className="text-right shrink-0 ml-3">
                    <span className="block text-xs font-bold text-[#a83428]">
                      waste {currentTransfer.strategies.noAction.waste}u
                    </span>
                    <span className="block text-xs font-semibold text-[#a83428]">
                      ₹ {currentTransfer.strategies.noAction.financial.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* 2. Markdown */}
              <div
                onClick={() => setSelectedStrategyType("markdown")}
                className={`cursor-pointer rounded-2xl border p-3.5 transition ${
                  selectedStrategyType === "markdown"
                    ? "border-[#a5b4a8] bg-[#f8faf8] ring-1 ring-[#a5b4a8]"
                    : "border-[#e5ece5] bg-white hover:bg-[#fafbfa]"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <strong className="block text-xs font-bold text-[#1a2d20]">
                      Markdown
                    </strong>
                    <p className="mt-1 text-[11.5px] leading-snug text-[#607466]">
                      {currentTransfer.strategies.markdown.desc}
                    </p>
                  </div>
                  <div className="text-right shrink-0 ml-3">
                    <span className="block text-xs font-bold text-[#10b981]">
                      waste {currentTransfer.strategies.markdown.waste}u
                    </span>
                    <span className={`block text-xs font-semibold ${
                      currentTransfer.strategies.markdown.financial > 0 ? "text-[#15803d]" : "text-[#a83428]"
                    }`}>
                      {currentTransfer.strategies.markdown.financial > 0 ? "+" : ""}₹ {currentTransfer.strategies.markdown.financial.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* 3. Transfer (Flagship Green Recommended Card!) */}
              <div
                onClick={() => setSelectedStrategyType("transfer")}
                className={`cursor-pointer rounded-2xl border p-3.5 transition ${
                  selectedStrategyType === "transfer"
                    ? "border-[#6dd6a5] bg-[#edf8f2] shadow-sm ring-1 ring-[#6dd6a5]"
                    : "border-[#96ddb9] bg-[#f4faf6] hover:bg-[#ebf7f0]"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <strong className="text-xs font-bold text-[#134932]">
                        Transfer
                      </strong>
                      <span className={`rounded-full px-1.5 py-0.2 text-[9px] font-bold text-white ${
                        currentTransfer.isFeasible ? "bg-[#10b981]" : "bg-[#ef4444]"
                      }`}>
                        {currentTransfer.isFeasible ? "OPTIMAL" : "AT-RISK"}
                      </span>
                    </div>
                    <p className="mt-1 text-[11.5px] leading-snug text-[#345b46]">
                      {currentTransfer.strategies.transfer.desc}
                    </p>
                  </div>
                  <div className="text-right shrink-0 ml-3">
                    <span className="block text-xs font-bold text-[#15803d]">
                      waste {currentTransfer.strategies.transfer.waste}u
                    </span>
                    <span className={`block text-xs font-bold ${
                      currentTransfer.strategies.transfer.financial >= 0 ? "text-[#15803d]" : "text-[#dc2626]"
                    }`}>
                      {currentTransfer.strategies.transfer.financial >= 0 ? "+" : ""}₹{currentTransfer.strategies.transfer.financial.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* 4. Reduce Order */}
              <div
                onClick={() => setSelectedStrategyType("reduceOrder")}
                className={`cursor-pointer rounded-2xl border p-3.5 transition ${
                  selectedStrategyType === "reduceOrder"
                    ? "border-[#a5b4a8] bg-[#f8faf8] ring-1 ring-[#a5b4a8]"
                    : "border-[#e5ece5] bg-white hover:bg-[#fafbfa]"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <strong className="block text-xs font-bold text-[#1a2d20]">
                      Reduce Order
                    </strong>
                    <p className="mt-1 text-[11.5px] leading-snug text-[#607466]">
                      {currentTransfer.strategies.reduceOrder.desc}
                    </p>
                  </div>
                  <div className="text-right shrink-0 ml-3">
                    <span className="block text-xs font-bold text-[#718576]">
                      waste {currentTransfer.strategies.reduceOrder.waste}u
                    </span>
                    <span className="block text-xs font-semibold text-[#a83428]">
                      ₹ {currentTransfer.strategies.reduceOrder.financial.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Descriptive Narrative Box */}
          <div className="mt-5 border-t border-[#edf2ec] pt-4">
            <p className="text-[11.5px] leading-relaxed text-[#5a7062]">
              {currentTransfer.summaryText}
            </p>

            <button
              onClick={() => handleDispatch(currentTransfer)}
              className={`mt-4 flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold text-white shadow transition ${
                currentTransfer.isFeasible
                  ? "bg-[#186441] hover:bg-[#135134]"
                  : "bg-[#b91c1c] hover:bg-[#991b1b]"
              }`}
            >
              <CheckCircle2 size={14} />
              <span>
                {currentTransfer.isFeasible
                  ? `Dispatch ${currentTransfer.qty} Units (${currentTransfer.route})`
                  : "Override & Force Dispatch (Not Recommended)"}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          SECTION: PROPOSED TRANSFERS & TRANSFER HISTORY TABLE
          (Exact visual fidelity from User's uploaded screenshot)
         ───────────────────────────────────────────────────────────── */}
      <div className="rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-sm space-y-5">
        {/* Table Top Header and Mode Switcher */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#edf2ec] pb-4">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold tracking-tight text-[#16271e]">
              Proposed transfers
            </h2>

            {/* Tab Pill Selector */}
            <div className="flex items-center rounded-xl bg-[#f0f4f0] p-1 text-xs">
              <button
                onClick={() => setActiveTab("proposals")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1 font-bold transition ${
                  activeTab === "proposals"
                    ? "bg-white text-[#186441] shadow-xs"
                    : "text-[#5e7165] hover:text-[#16271e]"
                }`}
              >
                <Truck size={13} />
                <span>Active Proposals</span>
                <span className="rounded-full bg-[#10b981]/20 px-1.5 py-0.2 text-[10px] font-bold text-[#107049]">
                  {PROPOSED_TRANSFERS.length}
                </span>
              </button>

              <button
                onClick={() => setActiveTab("history")}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1 font-bold transition ${
                  activeTab === "history"
                    ? "bg-white text-[#186441] shadow-xs"
                    : "text-[#5e7165] hover:text-[#16271e]"
                }`}
              >
                <History size={13} />
                <span>Transfer History</span>
                <span className="rounded-full bg-[#e2e8f0] px-1.5 py-0.2 text-[10px] font-bold text-[#475569]">
                  {PAST_TRANSFER_HISTORY.length}
                </span>
              </button>
            </div>
          </div>

          {/* Search and Filters Bar */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative min-w-[200px]">
              <Search
                size={13}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7f9386]"
              />
              <input
                type="text"
                placeholder="Search product or batch..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-[#d6e0d7] bg-[#fbfdfb] py-1.5 pl-8 pr-3 text-xs text-[#1c2e22] placeholder-[#8ea093] focus:border-[#10b981] focus:bg-white focus:outline-none"
              />
            </div>

            {/* Filter by Route */}
            {activeTab === "proposals" && (
              <select
                value={routeFilter}
                onChange={(e) => setRouteFilter(e.target.value)}
                className="rounded-xl border border-[#d6e0d7] bg-[#fbfdfb] px-2.5 py-1.5 text-xs font-semibold text-[#3b5243] focus:border-[#10b981] focus:outline-none"
              >
                <option value="ALL">All Routes</option>
                <option value="C_TO_B">Route C → B</option>
                <option value="A_TO_B">Route A → B</option>
              </select>
            )}

            {/* Filter by Feasibility */}
            {activeTab === "proposals" && (
              <select
                value={feasibilityFilter}
                onChange={(e) =>
                  setFeasibilityFilter(
                    e.target.value as "ALL" | "FEASIBLE" | "LOW_SHELF"
                  )
                }
                className="rounded-xl border border-[#d6e0d7] bg-[#fbfdfb] px-2.5 py-1.5 text-xs font-semibold text-[#3b5243] focus:border-[#10b981] focus:outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="FEASIBLE">Feasible Only</option>
                <option value="LOW_SHELF">Shelf Life Warning Only</option>
              </select>
            )}
          </div>
        </div>

        {/* ── Table View: Proposed Transfers ── */}
        {activeTab === "proposals" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#edf2ec] text-[11px] font-semibold text-[#718576]">
                  <th className="py-3 px-3 font-semibold">Product</th>
                  <th className="py-3 px-3 font-semibold">Route</th>
                  <th className="py-3 px-3 font-semibold text-right">Qty</th>
                  <th className="py-3 px-3 font-semibold text-right">Transport cost</th>
                  <th className="py-3 px-3 font-semibold text-right">Travel</th>
                  <th className="py-3 px-3 font-semibold text-right">Shelf at arrival</th>
                  <th className="py-3 px-4 font-semibold text-left">Feasibility</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f2f6f2] text-xs">
                {filteredProposals.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-xs text-[#718576]">
                      No proposed transfers match the filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredProposals.map((item) => {
                    const isSelected = selectedTransferId === item.id;

                    return (
                      <tr
                        key={item.id}
                        onClick={() => setSelectedTransferId(item.id)}
                        className={`cursor-pointer transition group ${
                          isSelected
                            ? "bg-[#e0f7ea] font-medium"
                            : "hover:bg-[#f8faf8] text-[#1c2e22]"
                        }`}
                      >
                        {/* Product & Batch Code */}
                        <td className="py-3 px-3">
                          <div className="font-medium text-[#182a1f]">
                            {item.product}
                          </div>
                          <div className="font-mono text-[11px] text-[#718576] mt-0.5">
                            {item.batchCode}
                          </div>
                        </td>

                        {/* Route */}
                        <td className="py-3 px-3">
                          <span className="font-medium text-[#2d4234]">
                            {item.route}
                          </span>
                        </td>

                        {/* Qty */}
                        <td className="py-3 px-3 text-right font-mono font-medium text-[#182a1f]">
                          {item.qty}
                        </td>

                        {/* Transport cost */}
                        <td className="py-3 px-3 text-right font-mono text-[#203426]">
                          ₹{item.transportCost}
                        </td>

                        {/* Travel time */}
                        <td className="py-3 px-3 text-right font-mono text-[#203426]">
                          {item.travelHours}
                        </td>

                        {/* Shelf at arrival */}
                        <td className="py-3 px-3 text-right font-mono text-[#203426]">
                          {item.shelfAtArrival}
                        </td>

                        {/* Feasibility */}
                        <td className="py-3 px-4">
                          {item.isFeasible ? (
                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#059669]">
                              <Truck size={13} className="text-[#059669]" />
                              <span>Feasible</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs font-medium text-[#dc2626]">
                              <span>Shelf life at arrival too low</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* ── Table View: Transfer History (Past Dispatches Log) ── */}
        {activeTab === "history" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-[#5e7165] bg-[#f9fbf9] p-3 rounded-xl border border-[#edf2ec]">
              <div className="flex items-center gap-2">
                <ShieldCheck size={16} className="text-[#10b981]" />
                <span>
                  <strong>100% Cold-Chain Compliance:</strong> All previous transfers logged with telematics temperature logs and verified arrivals.
                </span>
              </div>
              <div className="font-mono font-bold text-[#186441]">
                Total Margin Saved: ₹4,340 · Waste Averted: 118 kg
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#edf2ec] text-[11px] font-semibold text-[#718576]">
                    <th className="py-3 px-3 font-semibold">Manifest #</th>
                    <th className="py-3 px-3 font-semibold">Product</th>
                    <th className="py-3 px-3 font-semibold">Route</th>
                    <th className="py-3 px-3 font-semibold text-right">Units</th>
                    <th className="py-3 px-3 font-semibold text-right">Fuel Cost</th>
                    <th className="py-3 px-3 font-semibold text-right">Margin Saved</th>
                    <th className="py-3 px-3 font-semibold text-right">Dispatched / Delivered</th>
                    <th className="py-3 px-3 font-semibold text-right">Driver / Vehicle</th>
                    <th className="py-3 px-4 font-semibold text-left">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f2f6f2] text-xs">
                  {filteredHistory.map((item) => (
                    <tr
                      key={item.id}
                      className="hover:bg-[#f8faf8] transition text-[#1c2e22]"
                    >
                      <td className="py-3 px-3 font-mono font-bold text-[#186441]">
                        {item.transferNumber}
                      </td>

                      <td className="py-3 px-3">
                        <div className="font-medium text-[#182a1f]">
                          {item.product}
                        </div>
                        <div className="font-mono text-[11px] text-[#718576] mt-0.5">
                          {item.batchCode}
                        </div>
                      </td>

                      <td className="py-3 px-3 font-medium text-[#2d4234]">
                        {item.route}
                      </td>

                      <td className="py-3 px-3 text-right font-mono font-semibold">
                        {item.qty} u ({item.wastePreventedKg} kg)
                      </td>

                      <td className="py-3 px-3 text-right font-mono text-[#5b7063]">
                        ₹{item.cost}
                      </td>

                      <td className="py-3 px-3 text-right font-mono font-bold text-[#15803d]">
                        +₹{item.marginGain.toLocaleString()}
                      </td>

                      <td className="py-3 px-3 text-right text-[11.5px] text-[#55695c]">
                        <div>{item.dispatchedAt}</div>
                        <div className="text-[10.5px] text-[#86998d]">
                          Arrived: {item.deliveredAt}
                        </div>
                      </td>

                      <td className="py-3 px-3 text-right text-[11.5px] text-[#55695c]">
                        <div>{item.driver}</div>
                        <div className="text-[10.5px] text-[#86998d]">
                          {item.vehicle}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-[#dcfce7] px-2.5 py-0.5 text-[11px] font-bold text-[#15803d]">
                          <Check size={11} strokeWidth={3} />
                          <span>{item.status}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer explanation note */}
        <div className="flex items-center justify-between border-t border-[#edf2ec] pt-3 text-[11px] text-[#718576]">
          <div className="flex items-center gap-1.5">
            <Info size={12} className="text-[#10b981]" />
            <span>
              Clicking any proposed transfer selects it and updates the comparative strategy evaluation and network map above.
            </span>
          </div>

          <div className="font-mono text-[10.5px] text-[#85988b]">
            Algorithm: Dynamic Shelf Routing v3.4 · Real-time Traffic Matrix
          </div>
        </div>
      </div>
    </div>
  );
}

/* Helper to render each Store Card on the Network Graph */
function renderStoreCard(
  node: StoreNode,
  isSelected: boolean,
  onSelect: () => void
) {
  const isGreen = node.borderColor === "green";

  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer w-[190px] rounded-2xl bg-white p-3.5 transition shadow-sm ${
        isGreen
          ? "border-2 border-[#10b981]"
          : "border-2 border-[#f59e0b]"
      } ${isSelected ? "ring-4 ring-[#10b981]/20 scale-102" : "hover:scale-101"}`}
    >
      <div className="flex items-baseline justify-between">
        <strong className="text-xs font-bold text-[#1c2e22]">
          {node.code} · {node.name}
        </strong>
      </div>

      <p className="mt-0.5 text-[10px] text-[#6d8274]">
        Health {node.health} · {node.highRiskSkus} high-risk SKUs
      </p>

      <div className="mt-2.5 flex items-center justify-between text-[11px] font-semibold">
        <span className="text-[#d97706]">
          Surplus {node.surplusUnits}u
        </span>
        <span className="text-[#0284c7]">
          Short {node.shortUnits}u
        </span>
      </div>

      <div className="mt-2 border-t border-[#f2f6f2] pt-1.5 text-[11.5px] font-bold text-[#1c2e22]">
        ₹{node.valuation.toLocaleString()}
      </div>
    </div>
  );
}
