"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTeams } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const { data: teams, isLoading, isError } = useTeams();

  useEffect(() => {
    if (teams && teams.length > 0) {
      router.replace(`/teams/${teams[0].id}`);
    }
  }, [teams, router]);

  return (
    <main className="flex min-h-screen items-center justify-center p-8 text-sm text-slate-500">
      {isError
        ? "Could not reach the backend. Is the API running?"
        : isLoading
        ? "Loading your teams…"
        : teams && teams.length === 0
        ? "You do not have access to any teams."
        : "Opening your team…"}
    </main>
  );
}
