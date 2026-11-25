"use client";

import { toast } from "sonner";
import { useRateMeeting } from "@/lib/api";
import { ApiError } from "@/lib/api-client";
import { useUser } from "@/lib/user-context";
import type { MeetingState, User } from "@/types";
import { TodosSection } from "@/components/sections/todos-section";

export function ConcludePanel({
  teamId,
  state,
  me,
  readOnly,
}: {
  teamId: string;
  state: MeetingState;
  me: User;
  readOnly: boolean;
}) {
  const { userId } = useUser();
  const rate = useRateMeeting(teamId);
  const myRating = state.ratings.values[userId];
  const isAttendee = state.attendees.some((a) => a.id === userId);
  const canRate = !readOnly && isAttendee;

  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">Rate this meeting</h3>
          <span className="text-xs text-slate-400">
            avg {state.ratings.average ?? "—"} · {state.ratings.count} rating
            {state.ratings.count === 1 ? "" : "s"}
          </span>
        </div>
        {canRate ? (
          <div className="flex flex-wrap gap-1.5">
            {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
              <button
                key={n}
                onClick={() =>
                  rate.mutate(
                    { meetingId: state.id, rating: n },
                    { onError: (e) => toast.error(e instanceof ApiError ? e.message : "Failed") }
                  )
                }
                className={`h-9 w-9 rounded-md border text-sm font-medium transition-colors ${
                  myRating === n
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">
            {readOnly ? "Observers do not rate meetings." : "Join the meeting to rate it."}
          </p>
        )}
      </div>

      <TodosSection teamId={teamId} readOnly={readOnly} />
    </div>
  );
}
