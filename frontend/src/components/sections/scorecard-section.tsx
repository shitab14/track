"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Flag } from "lucide-react";
import { useMakeIssue, useSaveScore, useScorecard } from "@/lib/api";
import { ApiError } from "@/lib/api-client";
import { fmtDate, goalText, num, statusCell } from "@/lib/format";
import type { ScoreCell, ScorecardMeasurable } from "@/types";
import { SectionCard } from "./section-card";

function addDays(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

interface CellProps {
  cell: ScoreCell | null;
  weekStart: string;
  measurableId: string;
  readOnly: boolean;
  isCurrent: boolean;
  onSave: (value: number) => void;
  onMakeIssue: () => void;
}

function Cell({ cell, readOnly, isCurrent, onSave, onMakeIssue }: CellProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState<string>(cell ? String(cell.value) : "");
  const status = cell ? cell.status : isCurrent ? "pending" : "off_track";

  const commit = () => {
    setEditing(false);
    const trimmed = value.trim();
    if (trimmed === "" || (cell && trimmed === String(cell.value))) return;
    const n = Number(trimmed);
    if (!Number.isFinite(n)) {
      toast.error("Enter a number");
      setValue(cell ? String(cell.value) : "");
      return;
    }
    onSave(n);
  };

  if (editing) {
    return (
      <td className="p-0.5">
        <input
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") {
              setValue(cell ? String(cell.value) : "");
              setEditing(false);
            }
          }}
          className="h-8 w-16 rounded border border-slate-400 px-1 text-center text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          inputMode="decimal"
        />
      </td>
    );
  }

  return (
    <td className="p-0.5">
      <div
        className={`group relative flex h-8 w-16 items-center justify-center rounded text-sm ${statusCell[status]} ${
          readOnly ? "" : "cursor-pointer hover:ring-1 hover:ring-slate-300"
        }`}
        onClick={readOnly ? undefined : () => setEditing(true)}
        title={readOnly ? undefined : "Click to edit"}
      >
        <span>{cell ? num(cell.value) : "—"}</span>
        {!readOnly && cell && status === "off_track" && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMakeIssue();
            }}
            className="absolute -right-1 -top-1 hidden rounded-full bg-rose-600 p-0.5 text-white shadow group-hover:block"
            title="Make it an Issue"
          >
            <Flag className="h-3 w-3" />
          </button>
        )}
      </div>
    </td>
  );
}

export function ScorecardSection({ teamId, readOnly }: { teamId: string; readOnly: boolean }) {
  const { data, isLoading, isError } = useScorecard(teamId);
  const saveScore = useSaveScore(teamId);
  const makeIssue = useMakeIssue(teamId);

  if (isLoading) return <SectionCard title="Scorecard">Loading…</SectionCard>;
  if (isError || !data) return <SectionCard title="Scorecard">Could not load the scorecard.</SectionCard>;

  const currentWeek = data.weeks.length ? addDays(data.weeks[data.weeks.length - 1], 7) : "";
  const columns = [...data.weeks, currentWeek];

  const save = (m: ScorecardMeasurable, weekStart: string, value: number) =>
    saveScore.mutate(
      { measurable_id: m.id, week_start: weekStart, value },
      {
        onSuccess: () => toast.success(`${m.name} saved`),
        onError: (e) => toast.error(e instanceof ApiError ? e.message : "Save failed"),
      }
    );

  const promote = (cell: ScoreCell | null, m: ScorecardMeasurable) => {
    if (!cell) return;
    makeIssue.mutate(
      { scoreId: cell.id },
      {
        onSuccess: (res: any) =>
          toast.success(res?.message === "Issue already exists" ? "Issue already exists" : "Issue created"),
        onError: (e) => toast.error(e instanceof ApiError ? e.message : "Could not create issue"),
      }
    );
  };

  return (
    <SectionCard title="Scorecard" subtitle="Last 13 weeks · click a cell to edit">
      <div className="overflow-x-auto">
        <table className="w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-white px-2 py-2 text-left text-xs font-medium text-slate-500">
                Measurable
              </th>
              {columns.map((w, i) => (
                <th
                  key={w}
                  className={`px-1 py-2 text-center text-xs font-medium ${
                    i === columns.length - 1 ? "text-slate-900" : "text-slate-500"
                  }`}
                >
                  {fmtDate(w)}
                  {i === columns.length - 1 && <div className="text-[10px] font-normal text-slate-400">this wk</div>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.measurables.map((m) => (
              <tr key={m.id} className="border-t border-slate-100">
                <td className="sticky left-0 z-10 bg-white px-2 py-1.5">
                  <div className="font-medium text-slate-800">{m.name}</div>
                  <div className="text-xs text-slate-400">
                    {m.owner.name} · {goalText(m)} {m.unit}
                  </div>
                </td>
                {data.weeks.map((w) => (
                  <Cell
                    key={w}
                    cell={m.scores[w] ?? null}
                    weekStart={w}
                    measurableId={m.id}
                    readOnly={readOnly}
                    isCurrent={false}
                    onSave={(v) => save(m, w, v)}
                    onMakeIssue={() => promote(m.scores[w] ?? null, m)}
                  />
                ))}
                <Cell
                  cell={m.current_week_score}
                  weekStart={currentWeek}
                  measurableId={m.id}
                  readOnly={readOnly}
                  isCurrent
                  onSave={(v) => save(m, currentWeek, v)}
                  onMakeIssue={() => promote(m.current_week_score, m)}
                />
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}
