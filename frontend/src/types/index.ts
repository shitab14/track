export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

export type Role = "admin" | "team_member" | "observer";

export interface User {
  id: string;
  name: string;
  email?: string;
  role: Role;
}

export interface SeededUser {
  id: string;
  name: string;
  role: Role;
}

export interface Team {
  id: string;
  name: string;
  user_role?: Role;
}

export interface Owner {
  id: string;
  name: string;
}

export type MeasurableStatus = "on_track" | "off_track" | "pending";

export interface ScoreCell {
  id: number;
  value: string | number;
  status: MeasurableStatus;
}

export interface ScorecardMeasurable {
  id: string;
  name: string;
  unit: string;
  goal_type: "at_least" | "at_most" | "between" | "exactly" | string;
  goal_value: string | number | null;
  goal_min: string | number | null;
  goal_max: string | number | null;
  owner: Owner;
  scores: Record<string, ScoreCell>;
  current_week_score: ScoreCell | null;
}

export interface Scorecard {
  weeks: string[];
  measurables: ScorecardMeasurable[];
}

export interface IssueSource {
  measurable_id: string;
  week_start: string;
}

export interface Issue {
  id: string;
  title: string;
  priority: number | null;
  owner: Owner;
  source: IssueSource | null;
  created_at: string;
  resolution_note: string | null;
  solved_at: string | null;
}

export interface IssuesData {
  unsolved: Issue[];
  solved: Issue[];
}

export interface Todo {
  id: string;
  title: string;
  owner: Owner;
  due_date: string;
  done: boolean;
  overdue: boolean;
  source_issue_id: string | null;
  created_at: string;
  done_at: string | null;
}

export interface TodosData {
  completion_rate: number | null;
  todos: Todo[];
}

export interface Milestone {
  id: string;
  title: string;
  due_date: string;
  done: boolean;
  overdue: boolean;
}

export interface Rock {
  id: string;
  title: string;
  quarter: string;
  owner: Owner;
  computed_status: "on_track" | "off_track" | "complete";
  progress: { done: number; total: number; percent: number };
  milestones: Milestone[];
}

export type MeetingSection = "scorecard" | "ids" | "conclude" | "ended";

export interface Attendee {
  id: string;
  name: string;
  joined_at: string | null;
}

export interface MeetingRatings {
  values: Record<string, number>;
  count: number;
  average: number | null;
}

export interface MeetingState {
  id: string;
  team_id: string;
  facilitator_id: string;
  section: MeetingSection;
  section_started_at: string | null;
  section_budget_seconds: number | null;
  elapsed_seconds: number | null;
  over_time: boolean;
  server_now: string | null;
  started_at: string | null;
  ended_at: string | null;
  attendees: Attendee[];
  ratings: MeetingRatings;
}

export interface MeetingSummary {
  scorecard_week: string;
  measurable_status: Record<string, string>;
  issues_solved: string[];
  todos_created: string[];
  attendee_ids: string[];
  rating: number | null;
}
