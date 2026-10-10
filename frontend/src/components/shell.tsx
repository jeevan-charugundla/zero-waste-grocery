import { useState, type ReactNode } from "react";
import {
  Menu,
  X,
  Bell,
  Search,
  Calendar,
  Sparkles,
} from "lucide-react";
import { type RouteId, ROUTES } from "./routes";

export function AppShell({
  active,
  onNavigate,
  searchQuery,
  onSearchChange,
  children,
}: {
  active: RouteId;
  onNavigate: (id: RouteId) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  children: ReactNode;
}) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const activeRoute = ROUTES.find((r) => r.id === active) || ROUTES[2];

  return (
    <div className="flex min-h-screen bg-[#f4f7f4]">
      {/* Desktop Dark Forest Sidebar */}
      <Sidebar
        active={active}
        onNavigate={onNavigate}
        className="hidden lg:flex"
      />

      {/* Mobile Drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
            aria-hidden
          />
          <Sidebar
            active={active}
            onNavigate={(id) => {
              onNavigate(id);
              setDrawerOpen(false);
            }}
            className="absolute inset-y-0 left-0 flex w-[280px] shadow-2xl"
            onClose={() => setDrawerOpen(false)}
          />
        </div>
      )}

      {/* Main Content Column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          activeLabel={activeRoute.label}
          onMenu={() => setDrawerOpen(true)}
          searchQuery={searchQuery}
          onSearchChange={onSearchChange}
        />
        <main className="flex-1 px-4 py-6 sm:px-8 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

/* ---------- Sidebar (Dark Forest Theme from Screenshot) ---------- */

function Sidebar({
  active,
  onNavigate,
  className = "",
  onClose,
}: {
  active: RouteId;
  onNavigate: (id: RouteId) => void;
  className?: string;
  onClose?: () => void;
}) {
  return (
    <aside
      className={`w-[260px] shrink-0 flex-col bg-[#071d15] text-[#9fb3a7] py-6 px-4 select-none ${className}`}
      aria-label="FreshMind AI Navigation"
    >
      {/* Brand Header */}
      <div className="mb-7 flex items-center justify-between px-2">
        <div className="flex items-center gap-3">
          {/* Mint Leaf Icon Badge */}
          <div className="grid h-9 w-9 place-items-center rounded-full bg-[#10b981] text-[#071d15] shadow-md shadow-[#10b981]/20">
            <Sparkles size={18} className="fill-current" />
          </div>
          <div>
            <strong className="block text-[16px] font-extrabold tracking-tight text-white">
              FreshMind AI
            </strong>
            <span className="block text-[8.5px] font-bold tracking-[0.18em] text-[#34d399]">
              ZERO-WASTE OS
            </span>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-[#62776c] hover:bg-[#123828] hover:text-white"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Nav List */}
      <nav className="flex flex-col gap-1">
        {ROUTES.map(({ id, label, icon: Icon, badge }) => {
          const isActive = id === active;
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              className={`group flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-[13px] font-medium transition ${
                isActive
                  ? "bg-[#123828] font-bold text-white shadow-sm ring-1 ring-[#1b523b]"
                  : "text-[#8a9f93] hover:bg-[#0c2a1e] hover:text-[#d3e5db]"
              }`}
            >
              <Icon
                size={17}
                className={isActive ? "text-[#34d399]" : "text-[#657d70] group-hover:text-[#a0b8ab]"}
              />
              <span className="min-w-0 flex-1 truncate">{label}</span>
              {badge !== undefined && (
                <span className="ml-auto rounded-full bg-[#10b981] px-2 py-0.5 text-[10.5px] font-bold text-[#071d15]">
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Demo Network Badge */}
      <div className="mt-auto pt-6">
        <div className="rounded-2xl border border-[#143b2a] bg-[#0c271c] p-3.5 text-left">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#34d399] opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#10b981]" />
            </span>
            <span>Demo mode</span>
          </div>
          <p className="mt-1 text-[11px] font-medium text-[#7fa391]">
            Hyderabad Demo Network
          </p>
          <p className="mt-0.5 text-[9.5px] text-[#557563]">
            Synthetic data · agents simulated
          </p>
        </div>
      </div>
    </aside>
  );
}

/* ---------- Topbar ---------- */

function Topbar({
  activeLabel,
  onMenu,
  searchQuery,
  onSearchChange,
}: {
  activeLabel: string;
  onMenu: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-[#e1e7e1] bg-white/95 px-4 backdrop-blur-md sm:px-8">
      {/* Left: Menu trigger & Breadcrumb */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onMenu}
          className="rounded-lg p-1.5 text-[#4a5f52] hover:bg-[#f0f4f0] lg:hidden"
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>

        <div className="min-w-0">
          <span className="hidden text-[11px] font-semibold tracking-wide text-[#7d9285] sm:inline">
            FreshMind / {activeLabel}
          </span>
          <strong className="block text-[13px] font-bold text-[#1b2c22] sm:hidden">
            {activeLabel}
          </strong>
        </div>
      </div>

      {/* Center: Search input */}
      <div className="flex-1 max-w-md mx-2">
        <div className="relative">
          <Search
            size={15}
            className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8b9e93]"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search products or SKU..."
            className="w-full rounded-full border border-[#d6dfd6] bg-[#f8faf8] py-1.5 pl-9 pr-4 text-xs text-[#203227] placeholder-[#8b9e93] transition focus:border-[#10b981] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#10b981]/20"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        {/* Sim date badge */}
        <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-[#dce4dc] bg-[#f7faf7] px-3 py-1 text-[11px] font-medium text-[#465b4f]">
          <Calendar size={13} className="text-[#647c6d]" />
          <span>Sim date: 9 Oct 2026</span>
        </div>

        {/* DEMO amber pill */}
        <span className="rounded-full bg-[#fef3c7] px-2.5 py-0.5 text-[10.5px] font-bold text-[#b45309]">
          DEMO
        </span>

        {/* Notifications Bell */}
        <button
          className="relative rounded-full p-2 text-[#465b4f] hover:bg-[#f0f4f0] transition"
          aria-label="5 unread notifications"
        >
          <Bell size={17} />
          <span className="absolute right-1 top-1 grid h-4 w-4 place-items-center rounded-full bg-[#ef4444] text-[9.5px] font-bold text-white">
            5
          </span>
        </button>

        {/* User avatar MA */}
        <div className="grid h-8 w-8 place-items-center rounded-full bg-[#1b2c22] text-[11px] font-bold text-white shadow-sm">
          MA
        </div>
      </div>
    </header>
  );
}
