import { useState } from "react";
import { AlertOctagon, Flame, RefreshCw, CheckCircle2 } from "lucide-react";

export default function CrisisArenaPage() {
  const [shockSeverity, setShockSeverity] = useState(65);
  const [coldChainFailure, setColdChainFailure] = useState(true);
  const [unplannedSurplus, setUnplannedSurplus] = useState(true);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#16271e] sm:text-3xl flex items-center gap-2">
          <span>CrisisArena</span>
          <span className="rounded-full bg-[#fee2e2] text-[#dc2626] text-xs font-bold px-3 py-0.5">
            SIMULATION LAB
          </span>
        </h1>
        <p className="mt-1 text-sm text-[#5e7165]">
          Simulate black swan events, cold chain disruptions, sudden farm oversupply, and test agent coordination resilience.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Controls */}
        <div className="rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-[#1a2d21] flex items-center gap-2">
            <Flame size={18} className="text-[#f97316]" />
            <span>Crisis Parameters</span>
          </h2>

          <div>
            <div className="flex justify-between text-xs font-semibold text-[#4e6255]">
              <span>Supply Disruption Magnitude</span>
              <span>{shockSeverity}%</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              value={shockSeverity}
              onChange={(e) => setShockSeverity(Number(e.target.value))}
              className="mt-2 w-full accent-[#10b981]"
            />
          </div>

          <div className="space-y-3 pt-2">
            <label className="flex items-center gap-2.5 text-xs text-[#3b4e42] cursor-pointer">
              <input
                type="checkbox"
                checked={coldChainFailure}
                onChange={(e) => setColdChainFailure(e.target.checked)}
                className="rounded accent-[#10b981]"
              />
              <span className="font-medium">Chiller #2 Temperature Spike (+4°C)</span>
            </label>

            <label className="flex items-center gap-2.5 text-xs text-[#3b4e42] cursor-pointer">
              <input
                type="checkbox"
                checked={unplannedSurplus}
                onChange={(e) => setUnplannedSurplus(e.target.checked)}
                className="rounded accent-[#10b981]"
              />
              <span className="font-medium">Emergency Organic Farm Surplus (+120 kg Greens)</span>
            </label>
          </div>

          <button
            onClick={() => alert("Simulation executed. Autonomous agents rerouted 84% of affected batches.")}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-[#186441] py-2.5 text-xs font-bold text-white shadow hover:bg-[#135134] transition"
          >
            <RefreshCw size={14} />
            <span>Run Stress Simulation</span>
          </button>
        </div>

        {/* Results Preview */}
        <div className="lg:col-span-2 rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-[#1a2d21] flex items-center gap-2">
            <AlertOctagon size={18} className="text-[#ef4444]" />
            <span>Agent Mitigation Response</span>
          </h2>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-2xl border border-[#e5ece5] bg-[#f7faf7] p-4 text-center">
              <span className="text-xs text-[#718577]">Batches at Risk</span>
              <strong className="block text-xl font-bold text-[#b91c1c] mt-1">42 Batches</strong>
            </div>
            <div className="rounded-2xl border border-[#e5ece5] bg-[#f7faf7] p-4 text-center">
              <span className="text-xs text-[#718577]">Automated Rescue Rate</span>
              <strong className="block text-xl font-bold text-[#15803d] mt-1">88.4%</strong>
            </div>
            <div className="rounded-2xl border border-[#e5ece5] bg-[#f7faf7] p-4 text-center">
              <span className="text-xs text-[#718577]">Estimated Loss Avoided</span>
              <strong className="block text-xl font-bold text-[#1b2f23] mt-1">₹34,800</strong>
            </div>
          </div>

          <div className="rounded-2xl border border-[#e4ede4] bg-[#f4f8f4] p-4 text-xs space-y-2">
            <h4 className="font-bold text-[#1c2f23] flex items-center gap-2">
              <CheckCircle2 size={15} className="text-[#10b981]" />
              <span>Synthetic Resolution Plan Dispatched</span>
            </h4>
            <p className="text-[#4e6355] leading-relaxed">
              Markdown Agent triggered instant 40% clearance on 28 dairy units. Transfer Agent routed 14 surplus greens crates to Community Food Hub before peak transit heat window. Zero regulatory violations recorded.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
