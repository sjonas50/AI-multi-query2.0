"use client";

import { useState } from "react";
import type { Source } from "@/lib/citations";

interface SourcesPanelProps {
  sources: Source[];
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (sources.length === 0) return null;

  return (
    <div className="mt-3 border-t pt-3">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        <svg
          className={`h-3 w-3 transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        Sources ({sources.length})
      </button>
      {expanded && (
        <ul className="mt-2 space-y-1.5">
          {sources.map((s) => (
            <li key={s.index} className="flex items-start gap-2 text-xs">
              <span className="shrink-0 mt-0.5 w-4 h-4 rounded-full bg-muted flex items-center justify-center text-[10px] font-medium text-muted-foreground">
                {s.index}
              </span>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`https://www.google.com/s2/favicons?domain=${s.domain}&sz=16`}
                alt=""
                width={16}
                height={16}
                className="shrink-0 mt-0.5 rounded-sm"
              />
              <div className="min-w-0">
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline break-all"
                >
                  {s.title || s.domain}
                </a>
                {s.title && (
                  <span className="ml-1 text-muted-foreground">({s.domain})</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
