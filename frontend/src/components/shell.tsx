import { useState, useCallback, useEffect, type ReactNode } from "react";
import {
  ChevronDown,
  Menu,
  X,
  Bell,
  Wifi,
  WifiOff,
  RotateCw,
  LogOut,
  Settings,
} from "lucide-react";
import { DemoBadge } from "./ui";
import { type RouteId, ROUTES } from "./routes";
import { getHealth, explainHealthError, describeApiTarget, type ApiStatusState } from "../lib/api";

const recBadge: Partial<Record<RouteId, number>> = {
  recommendations: 4,
};

export function AppShell({
  active,
  onNavigate,
  children,
}: {
  active: RouteId;
  onNavigate: (id: RouteId) => void;
  children: ReactNode;
}) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiStatusState>({
    state: "checking",
  });

  const runHealthCheck = useCallback((force = false) => {
    if (!force && apiStatus.state === "checking") return; // already in flight
    setApiStatus({ state: "checking" });
    getHealth()
      .then(() => setApiStatus({ state: "connected" }))
      .catch((err: unknown) => {
        const reason = explainHealthError(err);
        setApiStatus({ state: "unavailable", reason });
      });
  }, [apiStatus.state]);

  const onRetry = useCallback(() => runHealthCheck(true), [runHealthCheck]);

  useEffect(() => {
    runHealthCheck();
    // No auto-retry loop: the user gets an explicit Retry button instead.
  }, [runHealthCheck]);

  const activeLabel = ROUTES.find((r) => r.id === active)?.label ?? "Overview";

  return (
    <div className="flex min-h-screen bg-[#f7f7f4]">
      {/* Desktop sidebar */}
      <Sidebar
        active={active}
        onNavigate={onNavigate}
        apiStatus={apiStatus}
        className="hidden lg:flex"
        onRetry={onRetry}
      />

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setDrawerOpen(false)}
            aria-hidden
          />
          <Sidebar
            active={active}
            onNavigate={(id) => {
              onNavigate(id);
              setDrawerOpen(false);
            }}
            apiStatus={apiStatus}
            className="absolute inset-y-0 left-0 flex w-[265px] shadow-xl"
            onClose={() => setDrawerOpen(false)}
            onRetry={onRetry}
          />
        </div>
      )}

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          activeLabel={activeLabel}
          onMenu={() => setDrawerOpen(true)}
          notifications={4}
        />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}

/* ---------- Sidebar ---------- */

function Sidebar({
  active,
  onNavigate,
  apiStatus,
  className = "",
  onClose,
  onRetry,
}: {
  active: RouteId;
  onNavigate: (id: RouteId) => void;
  apiStatus: ApiStatusState;
  className?: string;
  onClose?: () => void;
  onRetry: () => void;
}) {
  return (
    <aside
      className={`w-[248px] shrink-0 flex-col border-r border-[#e9ece7] bg-white py-5 px-3.5 ${className}`}
      aria-label="Primary navigation"
    >
      {/* Brand */}
      <div className="mb-6 flex items-center gap-2.5 px-2">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#287452] text-lg font-extrabold text-white">
          <span className="font-serif">f</span>
        </div>
        <div className="min-w-0 flex-1">
          <strong className="block text-[17px] leading-none tracking-tight text-[#25332c]">
            freshwise
          </strong>
          <small className="mt-1 block text-[8px] font-bold tracking-[0.14em] text-[#8b968e]">
            ZERO-WASTE INTELLIGENCE
          </small>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-md p-1 text-[#8b968e] hover:bg-[#f7f8f5] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]"
            aria-label="Close navigation"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Workspace selector */}
      <button
        className="mb-6 flex w-full items-center gap-2.5 rounded-xl border border-[#e9ece7] bg-[#f8f9f6] px-3 py-2.5 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40"
        aria-label="Workspace: Demo Grocery Network, press to switch workspace"
      >
        <span className="h-2 w-2 shrink-0 rounded-full bg-[#37866a]" />
        <div className="min-w-0 flex-1">
          <small className="block text-[9px] font-bold tracking-widest text-[#8a958d]">
            WORKSPACE
          </small>
          <strong className="block text-[11px] text-[#39473d]">
            Demo Grocery Network
          </strong>
        </div>
        <ChevronDown size={13} className="shrink-0 text-[#8a958d]" />
      </button>

      {/* Nav */}
      <nav className="mb-6 flex flex-col gap-1">
        <p className="px-3 pb-1.5 text-[9px] font-bold tracking-[0.14em] text-[#a0a9a1]">
          OPERATIONS
        </p>
        {ROUTES.map(({ id, label, icon: Icon }) => {
          const isActive = id === active;
          const badge = recBadge[id];
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              aria-current={isActive ? "page" : undefined}
              className={`group flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-[12.5px] transition ${
                isActive
                  ? "bg-[#eaf4ed] font-bold text-[#216b4a] shadow-[inset_2px_0_0_#287452]"
                  : "font-medium text-[#66736a] hover:bg-[#f7f8f5]"
              } focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40`}
            >
              <Icon
                size={16}
                className={isActive ? "text-[#287452]" : "text-[#7d8a80] group-hover:text-[#287452]"}
              />
              <span className="min-w-0 flex-1 truncate">{label}</span>
              {badge !== undefined && (
                <span className="ml-auto rounded-md bg-[#d3e8d8] px-1.5 py-0.5 text-[10px] font-bold text-[#236a4b]">
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col">
        <SidebarStatus
          apiStatus={apiStatus}
          onRetry={onRetry}
        />

        {/* User */}
        <div className="flex items-center gap-2.5 px-1 pb-1">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#e7e9de] text-[10px] font-bold text-[#56634f]">
            JM
          </div>
          <div className="min-w-0 flex-1">
            <strong className="block text-[11px] text-[#39473d]">Jordan Miller</strong>
            <small className="block text-[9.5px] text-[#8a958d]">Store manager · Demo</small>
          </div>
          <button
            className="rounded-md p-1 text-[#8a958d] hover:bg-[#f7f8f5] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]"
            aria-label="Sign out (demo only, no action)"
            tabIndex={-1}
          >
            <LogOut size={13} />
          </button>
          <button
            className="rounded-md p-1 text-[#8a958d] hover:bg-[#f7f8f5] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]"
            aria-label="Settings (demo only, no action)"
            tabIndex={-1}
          >
            <Settings size={13} />
          </button>
        </div>
      </div>
    </aside>
  );
}

/* ---------- Sidebar API status indicator ---------- */

function SidebarStatus({
  apiStatus,
  onRetry,
}: {
  apiStatus: ApiStatusState;
  onRetry: () => void;
}) {
  const [showDetail, setShowDetail] = useState(false);
  const apiTarget = describeApiTarget();

  const icon =
    apiStatus.state === "connected" ? (
      <Wifi size={13} className="text-green-600" aria-hidden />
    ) : apiStatus.state === "checking" ? (
      <span className="h-3.5 w-3.5 animate-pulse rounded-full bg-stone-300" aria-hidden />
    ) : (
      <WifiOff size={13} className="text-stone-400" aria-hidden />
  );

  const headline =
    apiStatus.state === "connected"
      ? "API connected"
      : apiStatus.state === "checking"
        ? "Checking API…"
        : "API unavailable";

  const subline =
    apiStatus.state === "connected"
      ? /* Health has no DB knowledge */ `FastAPI at ${apiTarget}`
      : apiStatus.state === "checking"
        ? `FastAPI at ${apiTarget}`
        : "Supabase status unknown · click to retry";

  return (
    <div className="mb-2.5 border-t border-[#edf0eb] px-1 pt-3 pb-2">
      <div className="flex items-center gap-2.5">
        {icon}
        <div className="min-w-0 flex-1">
          <strong className="block text-[10.5px] text-[#39473d]">{headline}</strong>
          <small className="block text-[9.5px] text-[#8a958d]">{subline}</small>
        </div>
        <button
          onClick={() => { onRetry(); setShowDetail(false); }}
          className="rounded-md p-1 text-[#8a958d] hover:bg-[#f7f8f5] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]"
          aria-label="Retry API connection check"
          title="Retry health check"
        >
          <RotateCw size={12} className={apiStatus.state === "checking" ? "animate-spin" : ""} />
    </button>
      </div>
      {apiStatus.state === "unavailable" && (
        <button
          onClick={() => setShowDetail((v) => !v)}
          className="mt-1.5 block text-left text-[9.5px] font-semibold text-[#b17a30] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]"
          aria-expanded={showDetail}
          aria-controls="api-status-detail"
          title="Show/hide connection diagnostic"
        >
          {showDetail ? "Hide details" : "Why? Show details"}
        </button>
      )}
      {apiStatus.state === "unavailable" && showDetail && (
        <p id="api-status-detail" className="mt-1 rounded-md bg-[#fdf4e5] px-2 py-1.5 text-[9.5px] leading-relaxed text-[#7a5a20]">
          {apiStatus.reason}
        </p>
      )}
    </div>
  );
}

/* ---------- Topbar ---------- */

function Topbar({
  activeLabel,
  onMenu,
  notifications,
}: {
  activeLabel: string;
  onMenu: () => void;
  notifications: number;
}) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-[#e8ece6] bg-white/90 px-4 backdrop-blur-sm sm:px-6">
      <div className="flex min-w-0 items-center gap-2.5">
        <button
          onClick={onMenu}
          className="rounded-md p-1.5 text-[#5c6b62] hover:bg-[#f7f8f5] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952] lg:hidden"
          aria-label="Open navigation menu"
        >
          <Menu size={18} />
        </button>
        <span className="hidden text-[11px] text-[#8a958d] sm:inline">Workspace</span>
        <ChevronDown size={11} className="hidden rotate-[-90deg] text-[#c2c9c1] sm:inline" />
        <strong className="truncate text-[12px] font-semibold text-[#39473d]">
          {activeLabel}
        </strong>
      </div>
      <div className="flex items-center gap-3">
        <DemoBadge />
        <button
          className="relative rounded-md p-1.5 text-[#68756c] hover:bg-[#f7f8f5] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]"
          aria-label={`Notifications, ${notifications} unread`}
        >
          <Bell size={16} />
          <span className="absolute right-0.5 top-0.5 h-1.5 w-1.5 rounded-full bg-red-500" />
        </button>
        <div className="hidden h-8 w-8 shrink-0 place-items-center rounded-full bg-[#e7e9de] text-[10px] font-bold text-[#56634f] sm:grid">
          JM
        </div>
      </div>
    </header>
  );
}
