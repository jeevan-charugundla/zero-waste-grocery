import {
  LayoutGrid,
  Boxes,
  TrendingUp,
  Sparkles,
  Package,
  Megaphone,
  HeartHandshake,
  MessagesSquare,
  Leaf,
} from "lucide-react";

export const ROUTES = [
  { id: "overview", label: "Overview", icon: LayoutGrid },
  { id: "inventory", label: "Inventory & expiry", icon: Boxes },
  { id: "forecasts", label: "Demand forecasts", icon: TrendingUp },
  { id: "recommendations", label: "AI recommendations", icon: Sparkles },
  { id: "bundles", label: "Smart bundles", icon: Package },
  { id: "campaigns", label: "Customer campaigns", icon: Megaphone },
  { id: "donations", label: "Donations & disposal", icon: HeartHandshake },
  { id: "copilot", label: "AI Store Copilot", icon: MessagesSquare },
  { id: "impact", label: "Impact & analytics", icon: Leaf },
] as const;

export type RouteId = (typeof ROUTES)[number]["id"];
