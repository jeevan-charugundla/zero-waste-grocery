import type { ReactNode } from "react";
import { Loader2, Inbox, AlertTriangle } from "lucide-react";

/* ---------- Badge ---------- */

export type BadgeTone =
  | "green"
  | "amber"
  | "red"
  | "violet"
  | "neutral"
  | "outline";

const badgeTones: Record<BadgeTone, string> = {
  green: "bg-green-50 text-green-700 border-green-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  red: "bg-red-50 text-red-700 border-red-200",
  violet: "bg-violet-50 text-violet-700 border-violet-200",
  neutral: "bg-stone-100 text-stone-600 border-stone-200",
  outline: "bg-white text-stone-500 border-stone-200",
};

export function Badge({
  tone = "neutral",
  children,
  className = "",
}: {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-[3px] text-[10px] font-semibold tracking-wide ${badgeTones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

/* ---------- Demo data badge ---------- */

export function DemoBadge({ label = "SIMULATED DATA" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-bold tracking-widest text-amber-700">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
      {label}
    </span>
  );
}

/* ---------- Panel (white card) ---------- */

export function Panel({
  title,
  subtitle,
  action,
  children,
  className = "",
  bodyClassName = "",
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={`rounded-xl border border-[#e6e8e3] bg-white shadow-[0_1px_2px_rgba(37,51,44,0.04)] ${className}`}
    >
      {(title || action) && (
        <header className="flex items-start justify-between gap-4 border-b border-[#eef0ec] px-4 py-3">
          <div className="min-w-0">
            {title && <h3 className="text-[13px] font-semibold text-[#2b3d30]">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-[11px] text-[#879188]">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div className={`px-4 py-3 ${bodyClassName}`}>{children}</div>
    </section>
  );
}

/* ---------- Page header ---------- */

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && (
          <span className="mb-2 block text-[9px] font-bold uppercase tracking-[0.13em] text-[#87948a]">
            {eyebrow}
          </span>
        )}
        <h1 className="text-[26px] font-bold leading-tight tracking-tight text-[#24372b]">
          {title}
        </h1>
        {subtitle && <p className="mt-1.5 max-w-2xl text-[12px] text-[#879188]">{subtitle}</p>}
      </div>
      {action && <div className="flex shrink-0 items-center gap-2">{action}</div>}
    </div>
  );
}

/* ---------- KPI card ---------- */

export function KpiCard({
  label,
  value,
  change,
  changeTone = "green",
  note,
  icon,
  explanation,
}: {
  label: string;
  value: string;
  change?: string;
  changeTone?: "green" | "red" | "amber" | "neutral";
  note?: string;
  icon: ReactNode;
  explanation?: string;
}) {
  const toneClass =
    changeTone === "green"
      ? "text-green-700"
      : changeTone === "red"
        ? "text-red-600"
        : changeTone === "amber"
          ? "text-amber-700"
          : "text-[#5c6b62]";
  return (
    <div
      className="rounded-xl border border-[#e6e8e3] bg-white p-4 shadow-[0_1px_2px_rgba(37,51,44,0.04)]"
      title={explanation}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold text-[#758178]">{label}</span>
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#f1f5f0] text-[#578066]">
          {icon}
        </span>
      </div>
      <div className="mt-2.5 text-[24px] font-bold tracking-tight text-[#2b3d30]">{value}</div>
      {(change || note) && (
        <div className="mt-1.5 flex flex-wrap items-baseline gap-x-1.5 text-[10px]">
          {change && <b className={`font-bold ${toneClass}`}>{change}</b>}
          {note && <span className="text-[#9aa39b]">{note}</span>}
        </div>
      )}
    </div>
  );
}

/* ---------- Buttons ---------- */

export function PrimaryButton({
  onClick,
  children,
  className = "",
  disabled = false,
  type = "button",
}: {
  onClick?: () => void;
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 rounded-lg bg-[#287452] px-3.5 py-2 text-[11px] font-bold text-white transition hover:bg-[#1b6143] disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
    >
      {children}
    </button>
  );
}

export function GhostButton({
  onClick,
  children,
  className = "",
  disabled = false,
}: {
  onClick?: () => void;
  children: ReactNode;
  className?: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-1.5 rounded-lg border border-[#e3e9e1] bg-white px-2.5 py-1.5 text-[10px] font-bold text-[#45614e] transition hover:bg-[#eff7f0] disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
    >
      {children}
    </button>
  );
}

export function LinkButton({
  onClick,
  children,
  className = "",
}: {
  onClick?: () => void;
  children: ReactNode;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-1.5 py-1 text-[10px] font-bold text-[#317956] transition hover:text-[#1b6143] ${className}`}
    >
      {children}
    </button>
  );
}

/* ---------- Select ---------- */

export function Select<T extends string>({
  value,
  onChange,
  options,
  ariaLabel,
  className = "",
}: {
  value: T;
  onChange: (v: T) => void;
  options: readonly { value: T; label: string }[];
  ariaLabel: string;
  className?: string;
}) {
  return (
    <select
      aria-label={ariaLabel}
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      className={`rounded-lg border border-[#e4e9e2] bg-white px-2.5 py-2 text-[11px] font-semibold text-[#45614e] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#227952]/40 ${className}`}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

/* ---------- Empty state ---------- */

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
      <span className="grid h-11 w-11 place-items-center rounded-xl bg-[#f1f5f0] text-[#889390]">
        {icon ?? <Inbox size={20} />}
      </span>
      <p className="text-[12px] font-semibold text-[#5c6b62]">{title}</p>
      {description && <p className="max-w-xs text-[11px] text-[#9aa39b]">{description}</p>}
      {action}
    </div>
  );
}

/* ---------- Skeletons ---------- */

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-[#eef0ec] ${className}`} />;
}

export function SkeletonRows({ rows = 3 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2.5">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
    </div>
  );
}

/* ---------- Error / warning notes ---------- */

export function InlineNote({
  tone = "amber",
  message,
}: {
  tone?: "amber" | "red" | "green" | "neutral";
  message: string;
  }) {
  const toneMap = {
    amber: "border-[#f0dfc0] bg-[#fdf4e5] text-[#7a5a20]",
    red: "border-[#f2d8d0] bg-[#fdf1ee] text-[#8f4a37]",
    green: "border-[#cfe7d8] bg-[#eaf6ef] text-[#1b6143]",
    neutral: "border-[#e6e8e3] bg-[#f7f7f4] text-[#5c6b62]",
  } as const;
  return (
    <div className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-[11px] ${toneMap[tone]}`}>
      {tone === "red" ? (
        <AlertTriangle size={13} className="mt-px shrink-0" />
      ) : tone === "green" ? (
        <Loader2 size={13} className="mt-px hidden shrink-0" aria-hidden />
      ) : (
        <AlertTriangle size={13} className="mt-px shrink-0 opacity-60" aria-hidden />
      )}
      <span>{message}</span>
    </div>
  );
}
