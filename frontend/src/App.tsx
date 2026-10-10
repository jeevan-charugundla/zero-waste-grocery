import { useState } from "react";
import { AppShell } from "./components/shell";
import type { RouteId } from "./components/routes";
import DecisionRoomPage from "./pages/DecisionRoomPage";
import OverviewPage from "./pages/OverviewPage";
import InventoryPage from "./pages/InventoryPage";
import StoreNetworkPage from "./pages/StoreNetworkPage";
import DonationsPage from "./pages/DonationsPage";
import CrisisArenaPage from "./pages/CrisisArenaPage";
import ImpactPage from "./pages/ImpactPage";
import ActivityApprovalsPage from "./pages/ActivityApprovalsPage";
import SettingsPage from "./pages/SettingsPage";
import "./styles/globals.css";

export default function App() {
  const [active, setActive] = useState<RouteId>("decision_room");
  const [searchQuery, setSearchQuery] = useState("");
  const [navKey, setNavKey] = useState(0);

  const navigate = (id: RouteId) => {
    setActive(id);
    setNavKey((k) => k + 1);
  };

  const page = (() => {
    switch (active) {
      case "decision_room":
        return <DecisionRoomPage searchQuery={searchQuery} />;
      case "overview":
        return <OverviewPage onNavigate={navigate} />;
      case "inventory":
        return <InventoryPage />;
      case "store_network":
        return <StoreNetworkPage />;
      case "food_rescue":
        return <DonationsPage />;
      case "crisis_arena":
        return <CrisisArenaPage />;
      case "analytics":
        return <ImpactPage />;
      case "activity":
        return <ActivityApprovalsPage />;
      case "settings":
        return <SettingsPage />;
      default:
        return <DecisionRoomPage searchQuery={searchQuery} />;
    }
  })();

  return (
    <AppShell
      active={active}
      onNavigate={navigate}
      searchQuery={searchQuery}
      onSearchChange={setSearchQuery}
    >
      <div key={navKey} className="w-full pb-10">
        {page}
        <footer className="mt-12 flex flex-col gap-1 border-t border-[#e2e7e2] pt-4 text-[11px] text-[#7a8e81] sm:flex-row sm:justify-between">
          <span>FreshMind AI · Zero-Waste OS · Hyderabad Demo Network</span>
          <span>Agent simulation deterministic mode — pure UI preview.</span>
        </footer>
      </div>
    </AppShell>
  );
}
