"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useUser } from "./user-context";
import type { MeetingState } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Subscribe to a meeting's SSE stream (ADR0009). The server sends the full
 * snapshot on connect and on every change; `data_changed` signals tell the
 * reused Team sections to refetch. EventSource auto-reconnects, and the
 * snapshot-on-connect re-syncs state, so late joins and reconnects are covered.
 */
export function useMeetingStream(
  meetingId: string | undefined,
  teamId: string,
  initial?: MeetingState | null
) {
  const { userId } = useUser();
  const qc = useQueryClient();
  const [state, setState] = useState<MeetingState | null>(initial ?? null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!meetingId) return;
    const url = `${BASE_URL}/meetings/${meetingId}/events?user_id=${encodeURIComponent(userId)}`;
    const es = new EventSource(url);

    es.addEventListener("meeting_state", (e) => {
      try {
        setState(JSON.parse((e as MessageEvent).data) as MeetingState);
        setConnected(true);
      } catch {
        /* ignore malformed frame */
      }
    });

    es.addEventListener("data_changed", (e) => {
      try {
        const { scope } = JSON.parse((e as MessageEvent).data) as { scope: string };
        qc.invalidateQueries({ queryKey: [scope, teamId] });
      } catch {
        /* ignore */
      }
    });

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false); // browser retries automatically

    return () => es.close();
  }, [meetingId, teamId, userId, qc]);

  return { state, connected };
}
