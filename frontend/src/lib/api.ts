"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest, ApiError } from "./api-client";
import { useUser } from "./user-context";
import type {
  IssuesData,
  MeetingState,
  MeetingSummary,
  Owner,
  Rock,
  Scorecard,
  SeededUser,
  Team,
  TodosData,
  User,
} from "@/types";

/** Shared query hook: keys include the acting user so a switch refetches. */
function useApiQuery<T>(key: (string | undefined)[], endpoint: string, enabled = true) {
  const { userId } = useUser();
  return useQuery({
    queryKey: [...key, userId],
    enabled,
    queryFn: async () => {
      const res = await apiRequest<T>(endpoint, { userId });
      return res.data as T;
    },
  });
}

// ---- Queries -------------------------------------------------------------
export const useMe = () => useApiQuery<User>(["me"], "/auth/me");
export const useUsers = () => useApiQuery<SeededUser[]>(["users"], "/auth/users");
export const useTeams = () => useApiQuery<Team[]>(["teams"], "/teams");

export const useScorecard = (teamId?: string) =>
  useApiQuery<Scorecard>(["scorecard", teamId], `/teams/${teamId}/scorecard`, !!teamId);
export const useIssues = (teamId?: string) =>
  useApiQuery<IssuesData>(["issues", teamId], `/teams/${teamId}/issues`, !!teamId);
export const useTodos = (teamId?: string) =>
  useApiQuery<TodosData>(["todos", teamId], `/teams/${teamId}/todos`, !!teamId);
export const useRocks = (teamId?: string) =>
  useApiQuery<Rock[]>(["rocks", teamId], `/teams/${teamId}/rocks`, !!teamId);
export const useMembers = (teamId?: string) =>
  useApiQuery<Owner[]>(["members", teamId], `/teams/${teamId}/members`, !!teamId);

// ---- Mutations -----------------------------------------------------------
function useTeamMutation<TArgs>(
  teamId: string | undefined,
  run: (args: TArgs, userId: string) => Promise<unknown>,
  invalidate: string[]
) {
  const { userId } = useUser();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: TArgs) => run(args, userId),
    onSuccess: () => {
      invalidate.forEach((resource) => qc.invalidateQueries({ queryKey: [resource, teamId] }));
    },
  });
}

const post = (endpoint: string, body: unknown, userId: string) =>
  apiRequest(endpoint, { method: "POST", body: JSON.stringify(body), userId });

export const useSaveScore = (teamId?: string) =>
  useTeamMutation<{ measurable_id: string; week_start: string; value: number }>(
    teamId,
    (b, userId) => post(`/teams/${teamId}/scores`, b, userId),
    ["scorecard"]
  );

export const useMakeIssue = (teamId?: string) =>
  useTeamMutation<{ scoreId: number }>(
    teamId,
    ({ scoreId }, userId) => post(`/scores/${scoreId}/make-issue`, {}, userId),
    ["issues", "scorecard"]
  );

export const useCreateIssue = (teamId?: string) =>
  useTeamMutation<{ title: string; priority: number | null }>(
    teamId,
    (b, userId) => post(`/teams/${teamId}/issues`, b, userId),
    ["issues"]
  );

export const useSetPriority = (teamId?: string) =>
  useTeamMutation<{ issueId: string; priority: number | null }>(
    teamId,
    ({ issueId, priority }, userId) =>
      apiRequest(`/issues/${issueId}/priority`, {
        method: "PATCH",
        body: JSON.stringify({ priority }),
        userId,
      }),
    ["issues"]
  );

export const useSolveIssue = (teamId?: string) =>
  useTeamMutation<{ issueId: string; resolution_note: string }>(
    teamId,
    ({ issueId, resolution_note }, userId) =>
      post(`/issues/${issueId}/solve`, { resolution_note }, userId),
    ["issues"]
  );

export const useAddTodo = (teamId?: string) =>
  useTeamMutation<{ issueId: string; title: string; owner_id: string; due_date?: string }>(
    teamId,
    ({ issueId, title, owner_id, due_date }, userId) =>
      post(`/issues/${issueId}/todos`, { title, owner_id, due_date }, userId),
    ["todos", "issues"]
  );

export const useToggleTodo = (teamId?: string) =>
  useTeamMutation<{ todoId: string; done: boolean }>(
    teamId,
    ({ todoId, done }, userId) => post(`/todos/${todoId}/${done ? "done" : "undo"}`, {}, userId),
    ["todos"]
  );

// ---- Meetings ------------------------------------------------------------
export const useActiveMeeting = (teamId?: string) =>
  useApiQuery<MeetingState | null>(
    ["active-meeting", teamId],
    `/teams/${teamId}/active-meeting`,
    !!teamId
  );

export const useMeetingSummary = (meetingId?: string) =>
  useApiQuery<MeetingSummary>(["summary", meetingId], `/meetings/${meetingId}/summary`, !!meetingId);

export const useStartMeeting = (teamId?: string) =>
  useTeamMutation<void>(teamId, (_args, userId) => post(`/teams/${teamId}/meetings`, {}, userId), [
    "active-meeting",
  ]);

export const useJoinMeeting = (teamId?: string) =>
  useTeamMutation<{ meetingId: string }>(
    teamId,
    ({ meetingId }, userId) => post(`/meetings/${meetingId}/join`, {}, userId),
    []
  );

export const useAdvanceMeeting = (teamId?: string) =>
  useTeamMutation<{ meetingId: string }>(
    teamId,
    ({ meetingId }, userId) => post(`/meetings/${meetingId}/advance`, {}, userId),
    []
  );

export const useEndMeeting = (teamId?: string) =>
  // Do not invalidate active-meeting here: the SSE "ended" snapshot keeps the
  // room mounted so it can render the immutable summary. Re-entering the route
  // refetches active-meeting (now null) and returns to the start screen.
  useTeamMutation<{ meetingId: string }>(
    teamId,
    ({ meetingId }, userId) => post(`/meetings/${meetingId}/end`, {}, userId),
    []
  );

export const useRateMeeting = (teamId?: string) =>
  useTeamMutation<{ meetingId: string; rating: number }>(
    teamId,
    ({ meetingId, rating }, userId) =>
      apiRequest(`/meetings/${meetingId}/rating`, {
        method: "PUT",
        body: JSON.stringify({ rating }),
        userId,
      }),
    []
  );

export { ApiError };
