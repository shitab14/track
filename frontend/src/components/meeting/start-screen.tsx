"use client";

import { toast } from "sonner";
import { useStartMeeting } from "@/lib/api";
import { ApiError } from "@/lib/api-client";
import type { User } from "@/types";
import { Button } from "@/components/ui/button";

export function StartScreen({ teamId, me }: { teamId: string; me: User }) {
  const start = useStartMeeting(teamId);
  const canStart = me.role !== "observer";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-10 text-center shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">No active meeting</h2>
      <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
        {canStart
          ? "Start the Level 10 Meeting to become the facilitator. Teammates can join from their own browsers."
          : "Ask an Admin or Team Member to start the meeting, then join here."}
      </p>
      {canStart && (
        <Button
          className="mt-4"
          disabled={start.isPending}
          onClick={() =>
            start.mutate(undefined, {
              onSuccess: () => toast.success("Meeting started"),
              onError: (e) => toast.error(e instanceof ApiError ? e.message : "Could not start"),
            })
          }
        >
          Start Level 10 Meeting
        </Button>
      )}
    </div>
  );
}
