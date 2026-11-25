"use client";

import { useActiveMeeting, useMe } from "@/lib/api";
import { Header } from "@/components/header";
import { MeetingRoom } from "@/components/meeting/meeting-room";
import { StartScreen } from "@/components/meeting/start-screen";

export default function MeetingPage({ params }: { params: { teamId: string } }) {
  const { teamId } = params;
  const { data: me } = useMe();
  const { data: active, isLoading } = useActiveMeeting(teamId);

  return (
    <>
      <Header activeTeamId={teamId} />
      <main className="mx-auto max-w-6xl px-4 py-6">
        {!me || isLoading ? (
          <p className="text-sm text-slate-500">Loading meeting…</p>
        ) : active ? (
          <MeetingRoom teamId={teamId} me={me} initial={active} />
        ) : (
          <StartScreen teamId={teamId} me={me} />
        )}
      </main>
    </>
  );
}
