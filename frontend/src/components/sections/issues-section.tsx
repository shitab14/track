"use client";

import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Plus } from "lucide-react";
import {
  useAddTodo,
  useCreateIssue,
  useIssues,
  useMembers,
  useSetPriority,
  useSolveIssue,
} from "@/lib/api";
import { ApiError } from "@/lib/api-client";
import { fmtDateTime } from "@/lib/format";
import type { Issue } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SectionCard } from "./section-card";

const PRIORITIES = ["5", "4", "3", "2", "1"];

function PriorityBadge({ priority }: { priority: number | null }) {
  if (priority == null) return <Badge className="bg-slate-100 text-slate-500">P–</Badge>;
  const tone = priority >= 4 ? "bg-rose-100 text-rose-700" : priority >= 2 ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600";
  return <Badge className={tone}>P{priority}</Badge>;
}

function errMsg(e: unknown) {
  return e instanceof ApiError ? e.message : "Something went wrong";
}

// ---- Create issue --------------------------------------------------------
const createSchema = z.object({ title: z.string().min(1, "Title is required"), priority: z.string() });

function CreateIssueDialog({ teamId }: { teamId: string }) {
  const [open, setOpen] = useState(false);
  const create = useCreateIssue(teamId);
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm({
    resolver: zodResolver(createSchema),
    defaultValues: { title: "", priority: "none" },
  });

  const submit = handleSubmit((v) => {
    create.mutate(
      { title: v.title, priority: v.priority === "none" ? null : Number(v.priority) },
      {
        onSuccess: () => {
          toast.success("Issue created");
          reset();
          setOpen(false);
        },
        onError: (e) => toast.error(errMsg(e)),
      }
    );
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Button size="sm" onClick={() => setOpen(true)}>
        <Plus className="h-4 w-4" /> New Issue
      </Button>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create issue</DialogTitle>
          <DialogDescription>You become the owner. Priority is optional.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <Input placeholder="Issue title" {...register("title")} />
            {errors.title && <p className="mt-1 text-xs text-rose-600">{errors.title.message}</p>}
          </div>
          <Controller
            control={control}
            name="priority"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No priority</SelectItem>
                  {PRIORITIES.map((p) => (
                    <SelectItem key={p} value={p}>
                      Priority {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={create.isPending}>
              Create
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ---- Solve issue ---------------------------------------------------------
const solveSchema = z.object({ resolution_note: z.string().min(1, "A note is required") });

function SolveDialog({ teamId, issue, open, onOpenChange }: { teamId: string; issue: Issue; open: boolean; onOpenChange: (o: boolean) => void }) {
  const solve = useSolveIssue(teamId);
  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(solveSchema),
    defaultValues: { resolution_note: "" },
  });

  const submit = handleSubmit((v) => {
    solve.mutate(
      { issueId: issue.id, resolution_note: v.resolution_note },
      {
        onSuccess: () => {
          toast.success("Issue solved");
          reset();
          onOpenChange(false);
        },
        onError: (e) => toast.error(errMsg(e)),
      }
    );
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Solve issue</DialogTitle>
          <DialogDescription>{issue.title}</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <textarea
              placeholder="How was it resolved?"
              rows={3}
              {...register("resolution_note")}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
            {errors.resolution_note && <p className="mt-1 text-xs text-rose-600">{errors.resolution_note.message}</p>}
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={solve.isPending}>
              Solve
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ---- Add To-Do -----------------------------------------------------------
const todoSchema = z.object({ title: z.string().min(1, "Title is required"), owner_id: z.string().min(1, "Owner is required") });

function AddTodoDialog({ teamId, issue, open, onOpenChange }: { teamId: string; issue: Issue; open: boolean; onOpenChange: (o: boolean) => void }) {
  const add = useAddTodo(teamId);
  const { data: members } = useMembers(teamId);
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm({
    resolver: zodResolver(todoSchema),
    defaultValues: { title: "", owner_id: "" },
  });

  const submit = handleSubmit((v) => {
    add.mutate(
      { issueId: issue.id, title: v.title, owner_id: v.owner_id },
      {
        onSuccess: () => {
          toast.success("To-Do added (due in 7 days)");
          reset();
          onOpenChange(false);
        },
        onError: (e) => toast.error(errMsg(e)),
      }
    );
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add a To-Do</DialogTitle>
          <DialogDescription>Linked to “{issue.title}”, due in 7 days.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <Input placeholder="To-Do title" {...register("title")} />
            {errors.title && <p className="mt-1 text-xs text-rose-600">{errors.title.message}</p>}
          </div>
          <div>
            <Controller
              control={control}
              name="owner_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Owner" />
                  </SelectTrigger>
                  <SelectContent>
                    {members?.map((m) => (
                      <SelectItem key={m.id} value={m.id}>
                        {m.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.owner_id && <p className="mt-1 text-xs text-rose-600">{errors.owner_id.message}</p>}
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={add.isPending}>
              Add
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ---- Row -----------------------------------------------------------------
function UnsolvedRow({ teamId, issue, readOnly }: { teamId: string; issue: Issue; readOnly: boolean }) {
  const setPriority = useSetPriority(teamId);
  const [solving, setSolving] = useState(false);
  const [adding, setAdding] = useState(false);

  return (
    <li className="flex flex-wrap items-center gap-2 border-b border-slate-100 py-2 last:border-0">
      {readOnly ? (
        <PriorityBadge priority={issue.priority} />
      ) : (
        <Select
          value={issue.priority == null ? "none" : String(issue.priority)}
          onValueChange={(v) =>
            setPriority.mutate(
              { issueId: issue.id, priority: v === "none" ? null : Number(v) },
              { onError: (e) => toast.error(errMsg(e)) }
            )
          }
        >
          <SelectTrigger className="h-7 w-20" aria-label="Priority">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">P–</SelectItem>
            {PRIORITIES.map((p) => (
              <SelectItem key={p} value={p}>
                P{p}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium text-slate-800">{issue.title}</div>
        <div className="text-xs text-slate-400">
          {issue.owner.name} · {fmtDateTime(issue.created_at)}
          {issue.source && ` · from ${issue.source.measurable_id} (wk ${issue.source.week_start})`}
        </div>
      </div>
      {!readOnly && (
        <div className="flex gap-1">
          <Button variant="subtle" size="xs" onClick={() => setAdding(true)}>
            + To-Do
          </Button>
          <Button variant="outline" size="xs" onClick={() => setSolving(true)}>
            Solve
          </Button>
        </div>
      )}
      <SolveDialog teamId={teamId} issue={issue} open={solving} onOpenChange={setSolving} />
      <AddTodoDialog teamId={teamId} issue={issue} open={adding} onOpenChange={setAdding} />
    </li>
  );
}

export function IssuesSection({ teamId, readOnly }: { teamId: string; readOnly: boolean }) {
  const { data, isLoading, isError } = useIssues(teamId);

  return (
    <SectionCard
      title="Issues"
      subtitle="Worked in priority order"
      action={!readOnly && data ? <CreateIssueDialog teamId={teamId} /> : undefined}
    >
      {isLoading ? (
        "Loading…"
      ) : isError || !data ? (
        "Could not load issues."
      ) : (
        <Tabs defaultValue="unsolved">
          <TabsList className="mb-3">
            <TabsTrigger value="unsolved">Unsolved ({data.unsolved.length})</TabsTrigger>
            <TabsTrigger value="solved">Solved ({data.solved.length})</TabsTrigger>
          </TabsList>
          <TabsContent value="unsolved">
            {data.unsolved.length === 0 ? (
              <p className="py-4 text-center text-slate-400">No open issues 🎉</p>
            ) : (
              <ul>
                {data.unsolved.map((i) => (
                  <UnsolvedRow key={i.id} teamId={teamId} issue={i} readOnly={readOnly} />
                ))}
              </ul>
            )}
          </TabsContent>
          <TabsContent value="solved">
            {data.solved.length === 0 ? (
              <p className="py-4 text-center text-slate-400">Nothing solved yet.</p>
            ) : (
              <ul>
                {data.solved.map((i) => (
                  <li key={i.id} className="border-b border-slate-100 py-2 last:border-0">
                    <div className="font-medium text-slate-700 line-through decoration-slate-300">{i.title}</div>
                    <div className="text-xs text-slate-400">
                      {i.owner.name} · solved {fmtDateTime(i.solved_at)}
                    </div>
                    {i.resolution_note && <p className="mt-1 text-xs text-slate-500">“{i.resolution_note}”</p>}
                  </li>
                ))}
              </ul>
            )}
          </TabsContent>
        </Tabs>
      )}
    </SectionCard>
  );
}
