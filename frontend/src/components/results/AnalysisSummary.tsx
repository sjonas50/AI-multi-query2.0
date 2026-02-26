"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import type { AnalysisData } from "@/lib/types";

export function AnalysisSummary({ data }: { data: AnalysisData }) {
  const [expanded, setExpanded] = useState(false);

  const sentimentColor =
    data.sentiment === "positive"
      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      : data.sentiment === "negative"
        ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
        : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200";

  return (
    <div className="mt-3 border-t pt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between text-sm font-medium text-muted-foreground hover:text-foreground"
      >
        <span>AISEO Analysis</span>
        <span>{expanded ? "Hide" : "Show"}</span>
      </button>

      {expanded && (
        <div className="mt-2 space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="font-medium">Sentiment:</span>
            <span className={`rounded px-2 py-0.5 text-xs ${sentimentColor}`}>
              {data.sentiment}
            </span>
          </div>

          {data.companies_mentioned.length > 0 && (
            <div>
              <span className="font-medium">Companies:</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {data.companies_mentioned.map((c) => (
                  <Badge key={c} variant="secondary" className="text-xs">
                    {c}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {data.authority_signals.length > 0 && (
            <div>
              <span className="font-medium">Authority signals:</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {data.authority_signals.map((s) => (
                  <Badge key={s} variant="outline" className="text-xs">
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {data.sources_cited.length > 0 && (
            <div>
              <span className="font-medium">Sources ({data.sources_cited.length}):</span>
              <ul className="mt-1 list-inside list-disc text-xs text-muted-foreground">
                {data.sources_cited.slice(0, 10).map((s) => (
                  <li key={s} className="truncate">
                    {s}
                  </li>
                ))}
                {data.sources_cited.length > 10 && (
                  <li>...and {data.sources_cited.length - 10} more</li>
                )}
              </ul>
            </div>
          )}

          {data.domain_statistics && (
            <div>
              <span className="font-medium">Domain distribution:</span>
              <div className="mt-1 grid grid-cols-3 gap-2 text-xs">
                <div className="rounded bg-muted p-1 text-center">
                  UGC {(data.domain_statistics as Record<string, number>).ugc_percentage?.toFixed(0) ?? 0}%
                </div>
                <div className="rounded bg-muted p-1 text-center">
                  Owned {(data.domain_statistics as Record<string, number>).owned_percentage?.toFixed(0) ?? 0}%
                </div>
                <div className="rounded bg-muted p-1 text-center">
                  Authority {(data.domain_statistics as Record<string, number>).authority_percentage?.toFixed(0) ?? 0}%
                </div>
              </div>
            </div>
          )}

          {data.negative_score != null && data.negative_score > 0 && (
            <div className="rounded bg-red-50 p-2 text-xs dark:bg-red-950">
              <span className="font-medium text-red-700 dark:text-red-300">
                Negative score: {data.negative_score}/100
              </span>
            </div>
          )}

          {data.optimization_insights && (
            <div>
              <span className="font-medium">Insights:</span>
              <p className="mt-1 text-xs text-muted-foreground">
                {typeof data.optimization_insights === "string"
                  ? data.optimization_insights.slice(0, 300)
                  : data.optimization_insights.join("; ").slice(0, 300)}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
