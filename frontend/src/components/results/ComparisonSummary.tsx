"use client";

import { ResponseViewer } from "./ResponseViewer";
import type { ComparisonResult } from "@/lib/types";

function ScoreBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value * 10));
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1.5 w-16 rounded-full bg-muted">
        <div
          className="h-1.5 rounded-full bg-foreground/70"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}

export function ComparisonSummary({ comparison }: { comparison: ComparisonResult }) {
  return (
    <div className="space-y-4">
      {/* Provider score cards */}
      <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
        {Object.entries(comparison.provider_rankings).map(([provider, ranking]) => (
          <div key={provider} className="rounded-md border p-3 text-sm">
            <div className="font-medium">{provider}</div>
            <div className="mt-1.5 space-y-1 text-xs text-muted-foreground">
              <div className="flex items-center justify-between">
                <span>Completeness</span>
                <ScoreBar value={ranking.completeness} />
              </div>
              <div className="flex items-center justify-between">
                <span>Accuracy</span>
                <ScoreBar value={ranking.accuracy_signals} />
              </div>
              <div className="flex items-center justify-between">
                <span>Sourcing</span>
                <ScoreBar value={ranking.sourcing} />
              </div>
            </div>
            {ranking.unique_value && (
              <p className="mt-2 text-xs italic text-muted-foreground">{ranking.unique_value}</p>
            )}
          </div>
        ))}
      </div>

      {/* Narrative summary */}
      <ResponseViewer content={comparison.summary} />
    </div>
  );
}
