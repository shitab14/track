"use client";

import { useEffect, useState } from "react";
import type { MeetingState } from "@/types";

function mmss(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/**
 * Server-owned timer, rendered client-side (ADR0009 decision 7): the snapshot
 * carries section_started_at, budget and server_now; we hold the clock offset
 * and tick locally, re-syncing on every snapshot.
 */
export function TimerBar({ state }: { state: MeetingState }) {
  const [now, setNow] = useState(() => Date.now());
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (state.server_now) setOffset(Date.now() - new Date(state.server_now).getTime());
  }, [state.server_now]);

  if (state.section === "ended" || !state.section_started_at || state.section_budget_seconds == null) {
    return null;
  }

  const startMs = new Date(state.section_started_at).getTime();
  const elapsed = (now - offset - startMs) / 1000;
  const budget = state.section_budget_seconds;
  const over = elapsed > budget;
  const shown = over ? elapsed - budget : budget - elapsed;
  const pct = Math.min(100, (elapsed / budget) * 100);

  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between">
        <span className={`font-mono text-2xl font-semibold ${over ? "text-rose-600" : "text-slate-900"}`}>
          {over ? "+" : ""}
          {mmss(shown)}
        </span>
        {over ? (
          <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700">Over time</span>
        ) : (
          <span className="text-xs text-slate-400">{mmss(budget)} budget</span>
        )}
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${over ? "bg-rose-500" : "bg-slate-800"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
