"use client";

import { toast } from "sonner";
import { Check, Undo2 } from "lucide-react";
import { useTodos, useToggleTodo } from "@/lib/api";
import { ApiError } from "@/lib/api-client";
import { fmtDate } from "@/lib/format";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionCard } from "./section-card";

function CompletionWidget({ rate }: { rate: number | null }) {
  if (rate == null) {
    return <span className="text-xs text-slate-400">No To-Dos due last week</span>;
  }
  const pct = Math.round(rate * 100);
  const meets = rate >= 0.9;
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-400">Last week</span>
      <Badge className={meets ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}>
        {pct}% {meets ? "✓" : "· target 90%"}
      </Badge>
    </div>
  );
}

export function TodosSection({ teamId, readOnly }: { teamId: string; readOnly: boolean }) {
  const { data, isLoading, isError } = useTodos(teamId);
  const toggle = useToggleTodo(teamId);

  return (
    <SectionCard
      title="To-Dos"
      action={data ? <CompletionWidget rate={data.completion_rate} /> : undefined}
    >
      {isLoading ? (
        "Loading…"
      ) : isError || !data ? (
        "Could not load to-dos."
      ) : data.todos.length === 0 ? (
        <p className="py-4 text-center text-slate-400">No to-dos.</p>
      ) : (
        <ul>
          {data.todos.map((t) => (
            <li key={t.id} className="flex items-center gap-3 border-b border-slate-100 py-2 last:border-0">
              {!readOnly && (
                <Button
                  variant={t.done ? "subtle" : "outline"}
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  title={t.done ? "Mark not done" : "Mark done"}
                  onClick={() =>
                    toggle.mutate(
                      { todoId: t.id, done: !t.done },
                      { onError: (e) => toast.error(e instanceof ApiError ? e.message : "Failed") }
                    )
                  }
                >
                  {t.done ? <Undo2 className="h-3.5 w-3.5" /> : <Check className="h-3.5 w-3.5" />}
                </Button>
              )}
              <div className="min-w-0 flex-1">
                <div className={`truncate ${t.done ? "text-slate-400 line-through" : "font-medium text-slate-800"}`}>
                  {t.title}
                </div>
                <div className="text-xs text-slate-400">
                  {t.owner.name} · due {fmtDate(t.due_date)}
                  {t.done && t.done_at && ` · done ${fmtDate(t.done_at)}`}
                </div>
              </div>
              {t.overdue && <Badge className="bg-rose-100 text-rose-700">Overdue</Badge>}
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}
