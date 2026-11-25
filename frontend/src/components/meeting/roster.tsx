"use client";

import { Crown } from "lucide-react";
import type { MeetingState } from "@/types";
import { useUser } from "@/lib/user-context";

export function Roster({ state }: { state: MeetingState }) {
  const { userId } = useUser();
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
        Attendees ({state.attendees.length})
      </h3>
      <ul className="space-y-1.5">
        {state.attendees.map((a) => {
          const isFacilitator = a.id === state.facilitator_id;
          const rating = state.ratings.values[a.id];
          return (
            <li key={a.id} className="flex items-center gap-2 text-sm">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-medium text-slate-600">
                {a.name.charAt(0)}
              </span>
              <span className="flex-1 truncate text-slate-700">
                {a.name}
                {a.id === userId && <span className="text-slate-400"> (you)</span>}
              </span>
              {isFacilitator && <Crown className="h-3.5 w-3.5 text-amber-500" />}
              {rating != null && (
                <span className="rounded bg-sky-100 px-1.5 text-xs font-medium text-sky-700">{rating}</span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
