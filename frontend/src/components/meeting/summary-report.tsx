"use client";

import { CheckCircle2 } from "lucide-react";
import { useMeetingSummary, useScorecard } from "@/lib/api";
import { fmtDate, statusDot } from "@/lib/format";
import type { MeasurableStatus, MeetingState } from "@/types";
import { Badge } from "@/components/ui/badge";

export function SummaryReport({ teamId, state }: { teamId: string; state: MeetingState }) {
  const { data: summary, isLoading } = useMeetingSummary(state.id);
  const { data: scorecard } = useScorecard(teamId);

  const measurableName = (id: string) =>
    scorecard?.measurables.find((m) => m.id === id)?.name ?? id;
  const attendeeName = (id: string) => state.attendees.find((a) => a.id === id)?.name ?? id;

  if (isLoading || !summary) {
    return <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">Loading summary…</div>;
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-emerald-600" />
        <h2 className="text-lg font-semibold text-slate-900">Meeting summary</h2>
        {summary.rating != null && (
          <Badge className="ml-auto bg-sky-100 text-sky-700">Rating {summary.rating}</Badge>
        )}
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Scorecard · week of {fmtDate(summary.scorecard_week)}
          </h3>
          <ul className="space-y-1">
            {Object.entries(summary.measurable_status).map(([mid, status]) => (
              <li key={mid} className="flex items-center gap-2 text-sm">
                <span className={`h-2 w-2 rounded-full ${statusDot[status as MeasurableStatus] ?? "bg-slate-300"}`} />
                <span className="text-slate-700">{measurableName(mid)}</span>
                <span className="ml-auto text-xs text-slate-400">{status.replace("_", " ")}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="space-y-4">
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Issues solved ({summary.issues_solved.length})
            </h3>
            <p className="text-sm text-slate-600">
              {summary.issues_solved.length ? summary.issues_solved.join(", ") : "None"}
            </p>
          </div>
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
              To-Dos created ({summary.todos_created.length})
            </h3>
            <p className="text-sm text-slate-600">
              {summary.todos_created.length ? summary.todos_created.join(", ") : "None"}
            </p>
          </div>
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Attendees ({summary.attendee_ids.length})
            </h3>
            <p className="text-sm text-slate-600">
              {summary.attendee_ids.map(attendeeName).join(", ")}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
