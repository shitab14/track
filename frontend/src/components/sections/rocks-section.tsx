"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useRocks } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { Rock } from "@/types";
import { Badge } from "@/components/ui/badge";
import { SectionCard } from "./section-card";

const statusTone: Record<string, string> = {
  on_track: "bg-emerald-100 text-emerald-700",
  off_track: "bg-rose-100 text-rose-700",
  complete: "bg-sky-100 text-sky-700",
};

const statusLabel: Record<string, string> = {
  on_track: "On track",
  off_track: "Off track",
  complete: "Complete",
};

function RockRow({ rock }: { rock: Rock }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="border-b border-slate-100 py-2 last:border-0">
      <button className="flex w-full items-center gap-2 text-left" onClick={() => setOpen((o) => !o)}>
        {open ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
        <div className="min-w-0 flex-1">
          <div className="truncate font-medium text-slate-800">{rock.title}</div>
          <div className="text-xs text-slate-400">
            {rock.owner.name} · {rock.quarter}
          </div>
        </div>
        <Badge className={statusTone[rock.computed_status] ?? "bg-slate-100 text-slate-600"}>
          {statusLabel[rock.computed_status] ?? rock.computed_status}
        </Badge>
        <div className="flex w-28 items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-slate-800" style={{ width: `${rock.progress.percent}%` }} />
          </div>
          <span className="w-9 text-right text-xs text-slate-500">{rock.progress.percent}%</span>
        </div>
      </button>
      {open && (
        <ul className="ml-6 mt-2 space-y-1">
          {rock.milestones.length === 0 && <li className="text-xs text-slate-400">No milestones.</li>}
          {rock.milestones.map((m) => (
            <li key={m.id} className="flex items-center gap-2 text-xs">
              <span className={m.done ? "text-emerald-600" : m.overdue ? "text-rose-600" : "text-slate-400"}>
                {m.done ? "✓" : "○"}
              </span>
              <span className={m.done ? "text-slate-400 line-through" : "text-slate-600"}>{m.title}</span>
              <span className="text-slate-400">· due {fmtDate(m.due_date)}</span>
              {!m.done && m.overdue && <Badge className="bg-rose-100 text-rose-700">Overdue</Badge>}
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

export function RocksSection({ teamId }: { teamId: string }) {
  const { data, isLoading, isError } = useRocks(teamId);

  return (
    <SectionCard title="Rocks" subtitle="This quarter's goals">
      {isLoading ? (
        "Loading…"
      ) : isError || !data ? (
        "Could not load rocks."
      ) : data.length === 0 ? (
        <p className="py-4 text-center text-slate-400">No rocks this quarter.</p>
      ) : (
        <ul>
          {data.map((r) => (
            <RockRow key={r.id} rock={r} />
          ))}
        </ul>
      )}
    </SectionCard>
  );
}
