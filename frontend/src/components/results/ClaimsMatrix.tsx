"use client";

import { useState, useMemo, Fragment } from "react";
import { Badge } from "@/components/ui/badge";
import type { Claim, ProviderRanking } from "@/lib/types";

const STATUS_CONFIG: Record<string, { icon: string; color: string }> = {
  agrees: { icon: "\u2713", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
  disagrees: { icon: "\u2715", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
  partially: { icon: "~", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" },
  not_mentioned: { icon: "\u2014", color: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400" },
};

interface ClaimsMatrixProps {
  claims: Claim[];
  rankings: Record<string, ProviderRanking>;
}

export function ClaimsMatrix({ claims, rankings }: ClaimsMatrixProps) {
  const providers = Object.keys(rankings);
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  const categories = useMemo(() => {
    const cats = new Set(claims.map((c) => c.category));
    return ["all", ...cats];
  }, [claims]);

  const filtered = categoryFilter === "all" ? claims : claims.filter((c) => c.category === categoryFilter);

  // Agreement summary
  const agreementStats = useMemo(() => {
    let allAgree = 0;
    let hasDisagree = 0;
    let partial = 0;
    for (const c of filtered) {
      const statuses = Object.values(c.providers);
      const mentioned = statuses.filter((s) => s !== "not_mentioned");
      if (mentioned.length === 0) continue;
      if (mentioned.every((s) => s === "agrees")) allAgree++;
      else if (mentioned.some((s) => s === "disagrees")) hasDisagree++;
      else partial++;
    }
    return { allAgree, hasDisagree, partial, total: filtered.length };
  }, [filtered]);

  return (
    <div className="space-y-3">
      {/* Category filters */}
      <div className="flex flex-wrap gap-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => { setCategoryFilter(cat); setExpandedRow(null); }}
            className={`rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors ${
              categoryFilter === cat
                ? "border-foreground bg-foreground text-background"
                : "border-input text-muted-foreground hover:bg-muted"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Agreement summary */}
      {agreementStats.total > 0 && (
        <div className="flex gap-3 text-xs text-muted-foreground">
          <span className="text-green-600 dark:text-green-400">{agreementStats.allAgree} all agree</span>
          <span className="text-yellow-600 dark:text-yellow-400">{agreementStats.partial} partial</span>
          <span className="text-red-600 dark:text-red-400">{agreementStats.hasDisagree} disagreements</span>
        </div>
      )}

      {/* Claims table */}
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="py-2 px-3 text-left font-medium">Claim</th>
              <th className="py-2 px-2 text-left font-medium">Type</th>
              {providers.map((p) => (
                <th key={p} className="py-2 px-2 text-center font-medium whitespace-nowrap">{p}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((claim, idx) => (
              <Fragment key={idx}>
                <tr
                  className="border-b cursor-pointer hover:bg-muted/30 transition-colors"
                  onClick={() => setExpandedRow(expandedRow === idx ? null : idx)}
                >
                  <td className="py-2 px-3 max-w-xs">{claim.claim}</td>
                  <td className="py-2 px-2">
                    <Badge variant="outline" className="text-[10px]">{claim.category}</Badge>
                  </td>
                  {providers.map((p) => {
                    const status = claim.providers[p] || "not_mentioned";
                    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.not_mentioned;
                    return (
                      <td key={p} className="py-2 px-2 text-center">
                        <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${cfg.color}`}>
                          {cfg.icon}
                        </span>
                      </td>
                    );
                  })}
                </tr>
                {expandedRow === idx && (
                  <tr>
                    <td colSpan={2 + providers.length} className="px-3 py-2 bg-muted/20">
                      <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${providers.length}, 1fr)` }}>
                        {providers.map((p) => (
                          <div key={p} className="text-xs">
                            <span className="font-medium">{p}</span>
                            <p className="mt-0.5 text-muted-foreground">
                              {claim.details[p] || "Not addressed"}
                            </p>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
