"use client";

import { useMe } from "@/lib/api";
import { Header } from "@/components/header";
import { ScorecardSection } from "@/components/sections/scorecard-section";
import { IssuesSection } from "@/components/sections/issues-section";
import { TodosSection } from "@/components/sections/todos-section";
import { RocksSection } from "@/components/sections/rocks-section";

export default function TeamPage({ params }: { params: { teamId: string } }) {
  const { teamId } = params;
  const { data: me } = useMe();
  const readOnly = me?.role === "observer";

  return (
    <>
      <Header activeTeamId={teamId} />
      <main className="mx-auto max-w-6xl space-y-5 px-4 py-6">
        {readOnly && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
            You are an Observer — this team is read-only.
          </div>
        )}
        <ScorecardSection teamId={teamId} readOnly={readOnly} />
        <div className="grid gap-5 lg:grid-cols-2">
          <IssuesSection teamId={teamId} readOnly={readOnly} />
          <TodosSection teamId={teamId} readOnly={readOnly} />
        </div>
        <RocksSection teamId={teamId} />
      </main>
    </>
  );
}
