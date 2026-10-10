import { CheckCircle2, XCircle, Clock, ShieldCheck, User } from "lucide-react";

const AUDIT_LOGS = [
  {
    id: "LOG-9921",
    action: "Approved Proposal R-105",
    details: "Spinach Bunch (47 units) routed to Community Food Hub donation",
    actor: "Jordan Miller (Store Manager)",
    time: "10 mins ago",
    type: "approval",
  },
  {
    id: "LOG-9920",
    action: "Approved Proposal R-101",
    details: "Whole Milk 1L (20 units) breakfast distribution approved",
    actor: "Jordan Miller (Store Manager)",
    time: "45 mins ago",
    type: "approval",
  },
  {
    id: "LOG-9919",
    action: "Simulated Agent Replenishment",
    details: "Demand Agent synchronized 3-day forecasting matrix",
    actor: "Autonomous Coordinator",
    time: "2 hours ago",
    type: "system",
  },
  {
    id: "LOG-9918",
    action: "Rejected Proposal R-098",
    details: "Manual override: organic apples markdown reduced from 50% to 25%",
    actor: "Assistant Manager",
    time: "4 hours ago",
    type: "rejection",
  },
];

export default function ActivityApprovalsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#16271e] sm:text-3xl">
          Activity & Approvals
        </h1>
        <p className="mt-1 text-sm text-[#5e7165]">
          Full auditable log of manager decisions, agent proposals, and physical clearance confirmations.
        </p>
      </div>

      <div className="rounded-3xl border border-[#dfe5df] bg-white p-6 shadow-sm">
        <div className="divide-y divide-[#edf2ed]">
          {AUDIT_LOGS.map((log) => (
            <div key={log.id} className="py-4 first:pt-0 last:pb-0 flex items-start gap-4">
              <div className="mt-1">
                {log.type === "approval" ? (
                  <CheckCircle2 size={18} className="text-[#10b981]" />
                ) : log.type === "rejection" ? (
                  <XCircle size={18} className="text-[#ef4444]" />
                ) : (
                  <ShieldCheck size={18} className="text-[#3b82f6]" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-[#1c2e22]">{log.action}</h4>
                  <span className="text-xs text-[#809587] flex items-center gap-1">
                    <Clock size={11} />
                    <span>{log.time}</span>
                  </span>
                </div>
                <p className="mt-1 text-xs text-[#526658]">{log.details}</p>
                <div className="mt-2 flex items-center gap-2 text-[11px] text-[#6b8071]">
                  <User size={11} />
                  <span>{log.actor}</span>
                  <span className="font-mono text-[#9bb0a3]">({log.id})</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
