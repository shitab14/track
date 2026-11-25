"use client";

import type { MeetingSection } from "@/types";

const STEPS: { key: MeetingSection; label: string; budget: string }[] = [
  { key: "scorecard", label: "Scorecard", budget: "5m" },
  { key: "ids", label: "IDS", budget: "60m" },
  { key: "conclude", label: "Conclude", budget: "10m" },
];

export function SectionNav({ section }: { section: MeetingSection }) {
  const activeIndex = STEPS.findIndex((s) => s.key === section);
  return (
    <ol className="flex items-center gap-2">
      {STEPS.map((step, i) => {
        const done = activeIndex > i || section === "ended";
        const active = section === step.key;
        return (
          <li key={step.key} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-2 rounded-full px-3 py-1 text-sm ${
                active
                  ? "bg-slate-900 text-white"
                  : done
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-slate-100 text-slate-500"
              }`}
            >
              <span className="font-medium">{step.label}</span>
              <span className="text-xs opacity-70">{step.budget}</span>
            </div>
            {i < STEPS.length - 1 && <span className="text-slate-300">→</span>}
          </li>
        );
      })}
    </ol>
  );
}
