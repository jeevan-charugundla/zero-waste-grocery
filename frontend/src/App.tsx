import { useState } from "react";
import { AppShell } from "./components/shell";
import type { RouteId } from "./components/routes";
import OverviewPage from "./pages/OverviewPage";
import InventoryPage from "./pages/InventoryPage";
import ForecastsPage from "./pages/ForecastsPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import BundlesPage from "./pages/BundlesPage";
import CampaignsPage from "./pages/CampaignsPage";
import DonationsPage from "./pages/DonationsPage";
import CopilotPage from "./pages/CopilotPage";
import ImpactPage from "./pages/ImpactPage";
import "./styles/globals.css";

export default function App() {
  const [active, setActive] = useState<RouteId>("overview");
  const [navKey, setNavKey] = useState(0);

  const navigate = (id: RouteId) => {
    setActive(id);
    setNavKey((k) => k + 1); // remount page content on section change
  };

  const page = (() => {
    switch (active) {
      case "overview":
        return <OverviewPage onNavigate={navigate} />;
      case "inventory":
        return <InventoryPage />;
      case "forecasts":
        return <ForecastsPage />;
      case "recommendations":
        return <RecommendationsPage />;
      case "bundles":
        return <BundlesPage />;
      case "campaigns":
        return <CampaignsPage />;
      case "donations":
        return <DonationsPage />;
      case "copilot":
        return <CopilotPage />;
      case "impact":
        return <ImpactPage />;
    }
  })();

  return (
    <AppShell active={active} onNavigate={navigate}>
      <div key={navKey} className="mx-auto max-w-[1500px] px-4 pb-10 pt-6 sm:px-6">
        {page}
        <footer className="mt-8 flex flex-col gap-1 border-t border-[#e8ece6] pt-4 text-[10px] text-[#9aa39b] sm:flex-row sm:justify-between">
          <span>Freshwise · Agentic AI for perishable inventory</span>
          <span>Demo workspace — replace illustrative values with validated backend results.</span>
        </footer>
      </div>
    </AppShell>
  );
}
