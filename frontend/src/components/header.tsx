"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Users } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useTeams, useUsers } from "@/lib/api";
import { useUser } from "@/lib/user-context";
import { roleLabel } from "@/lib/format";

const roleBadge: Record<string, string> = {
  admin: "bg-violet-100 text-violet-700",
  team_member: "bg-sky-100 text-sky-700",
  observer: "bg-amber-100 text-amber-700",
};

export function Header({ activeTeamId }: { activeTeamId: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const { userId, setUserId } = useUser();
  const { data: users } = useUsers();
  const { data: teams } = useTeams();

  const onMeeting = pathname?.endsWith("/meeting");
  const navLink = (active: boolean) =>
    `rounded-md px-2.5 py-1 text-xs font-medium ${active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"}`;

  const currentUser = users?.find((u) => u.id === userId);

  // If the active team is not accessible to the current user, move to the first one.
  useEffect(() => {
    if (teams && teams.length > 0 && !teams.some((t) => t.id === activeTeamId)) {
      router.replace(`/teams/${teams[0].id}`);
    }
  }, [teams, activeTeamId, router]);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-900 text-xs font-bold text-white">
            T
          </div>
          <span className="text-sm font-semibold tracking-tight text-slate-900">Track</span>
          {teams && teams.length > 0 && (
            <Select value={activeTeamId} onValueChange={(id) => router.push(`/teams/${id}`)}>
              <SelectTrigger className="ml-2 h-8 w-44" aria-label="Select team">
                <SelectValue placeholder="Select team" />
              </SelectTrigger>
              <SelectContent>
                {teams.map((t) => (
                  <SelectItem key={t.id} value={t.id}>
                    {t.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <nav className="ml-1 flex items-center gap-1">
            <Link href={`/teams/${activeTeamId}`} className={navLink(!onMeeting)}>
              Team
            </Link>
            <Link href={`/teams/${activeTeamId}/meeting`} className={navLink(!!onMeeting)}>
              Meeting
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {currentUser && (
            <Badge className={roleBadge[currentUser.role] ?? "bg-slate-100 text-slate-600"}>
              {roleLabel(currentUser.role)}
            </Badge>
          )}
          <Users className="h-4 w-4 text-slate-400" />
          <Select value={userId} onValueChange={setUserId}>
            <SelectTrigger className="h-8 w-48" aria-label="Switch user">
              <SelectValue placeholder="Switch user" />
            </SelectTrigger>
            <SelectContent>
              {users?.map((u) => (
                <SelectItem key={u.id} value={u.id}>
                  {u.name} · {roleLabel(u.role)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </header>
  );
}
