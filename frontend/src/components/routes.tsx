import {
  LayoutGrid,
  Boxes,
  BrainCircuit,
  Store,
  HeartHandshake,
  Zap,
  BarChart3,
  CheckCircle2,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavRoute {
  id: RouteId;
  label: string;
  icon: LucideIcon;
  badge?: number;
}

export type RouteId =
  | "overview"
  | "inventory"
  | "decision_room"
  | "store_network"
  | "food_rescue"
  | "crisis_arena"
  | "analytics"
  | "activity"
  | "settings";

export const ROUTES: readonly NavRoute[] = [
  { id: "overview", label: "Overview", icon: LayoutGrid },
  { id: "inventory", label: "Inventory & Freshness", icon: Boxes },
  { id: "decision_room", label: "AI Decision Room", icon: BrainCircuit, badge: 10 },
  { id: "store_network", label: "Store Network", icon: Store },
  { id: "food_rescue", label: "Food Rescue", icon: HeartHandshake },
  { id: "crisis_arena", label: "CrisisArena", icon: Zap },
  { id: "analytics", label: "Analytics & Impact", icon: BarChart3 },
  { id: "activity", label: "Activity & Approvals", icon: CheckCircle2 },
  { id: "settings", label: "Settings", icon: Settings },
];
