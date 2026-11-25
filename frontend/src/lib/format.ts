import type { MeasurableStatus, ScorecardMeasurable } from "@/types";

export function num(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v);
  return Number.isInteger(n) ? String(n) : String(parseFloat(n.toFixed(2)));
}

export function fmtDate(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function fmtDateTime(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function goalText(m: ScorecardMeasurable): string {
  switch (m.goal_type) {
    case "at_least":
      return `≥ ${num(m.goal_value)}`;
    case "at_most":
      return `≤ ${num(m.goal_value)}`;
    case "exactly":
      return `= ${num(m.goal_value)}`;
    case "between":
      return `${num(m.goal_min)}–${num(m.goal_max)}`;
    default:
      return "—";
  }
}

export const statusCell: Record<MeasurableStatus, string> = {
  on_track: "bg-emerald-50 text-emerald-700",
  off_track: "bg-rose-50 text-rose-700",
  pending: "bg-slate-50 text-slate-400",
};

export const statusDot: Record<MeasurableStatus, string> = {
  on_track: "bg-emerald-500",
  off_track: "bg-rose-500",
  pending: "bg-slate-300",
};

export function roleLabel(role: string): string {
  return role
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}
