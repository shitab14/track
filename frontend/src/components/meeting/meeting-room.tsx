"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useAdvanceMeeting, useEndMeeting, useJoinMeeting } from "@/lib/api";
import { ApiError } from "@/lib/api-client";
import { useMeetingStream } from "@/lib/use-meeting-stream";
import { useUser } from "@/lib/user-context";
import type { MeetingState, User } from "@/types";
import { Button } from "@/components/ui/button";
import { ScorecardSection } from "@/components/sections/scorecard-section";
import { IssuesSection } from "@/components/sections/issues-section";
import { TimerBar } from "./timer-bar";
import { SectionNav } from "./section-nav";
import { Roster } from "./roster";
import { ConcludePanel } from "./conclude-panel";
import { SummaryReport } from "./summary-report";

export function MeetingRoom({ teamId, me, initial }: { teamId: string; me: User; initial: MeetingState }) {
  const { userId } = useUser();
  const join = useJoinMeeting(teamId);
  const advance = useAdvanceMeeting(teamId);
  const end = useEndMeeting(teamId);
  const { state: streamed } = useMeetingStream(initial.id, teamId, initial);
  const state = streamed ?? initial;

  const joinedRef = useRef(false);
  useEffect(() => {
    if (!joinedRef.current) {
      joinedRef.current = true;
      join.mutate({ meetingId: initial.id });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial.id]);

  if (state.section === "ended") {
    return <SummaryReport teamId={teamId} state={state} />;
  }

  const readOnly = me.role === "observer";
  const isFacilitator = state.facilitator_id === userId;
  const nextLabel = state.section === "scorecard" ? "IDS" : state.section === "ids" ? "Conclude" : null;

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_260px]">
      <div className="space-y-5">
        <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <SectionNav section={state.section} />
            {isFacilitator && (
              <div className="flex gap-2">
                {nextLabel && (
                  <Button
                    size="sm"
                    onClick={() =>
                      advance.mutate(
                        { meetingId: state.id },
                        { onError: (e) => toast.error(e instanceof ApiError ? e.message : "Failed") }
                      )
                    }
                  >
                    → {nextLabel}
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() =>
                    end.mutate(
                      { meetingId: state.id },
                      {
                        onSuccess: () => toast.success("Meeting ended"),
                        onError: (e) => toast.error(e instanceof ApiError ? e.message : "Failed"),
                      }
                    )
                  }
                >
                  End
                </Button>
              </div>
            )}
          </div>
          <TimerBar state={state} />
        </div>

        {state.section === "scorecard" && <ScorecardSection teamId={teamId} readOnly={readOnly} />}
        {state.section === "ids" && <IssuesSection teamId={teamId} readOnly={readOnly} />}
        {state.section === "conclude" && (
          <ConcludePanel teamId={teamId} state={state} me={me} readOnly={readOnly} />
        )}
      </div>

      <Roster state={state} />
    </div>
  );
}
