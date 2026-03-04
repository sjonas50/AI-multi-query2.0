"use client";

import { useEffect, useRef } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ComparisonSummary } from "./ComparisonSummary";
import { ClaimsMatrix } from "./ClaimsMatrix";
import { DiffView } from "./DiffView";
import type { ProviderResult, ComparisonResult } from "@/lib/types";

type ComparisonStatus = "idle" | "loading" | "complete" | "error";

interface ComparisonPanelProps {
  query: string;
  results: Map<string, ProviderResult> | ProviderResult[];
  comparison: ComparisonResult | null;
  comparisonStatus: ComparisonStatus;
  comparisonError: string | null;
  onGenerate: (query: string, results: Map<string, ProviderResult> | ProviderResult[]) => void;
  onReset: () => void;
}

export function ComparisonPanel({
  query,
  results,
  comparison,
  comparisonStatus: status,
  comparisonError: error,
  onGenerate: generate,
  onReset: reset,
}: ComparisonPanelProps) {
  const autoTriggered = useRef(false);

  // Count eligible providers (successful LLM text responses, not Google Search)
  const entries: [string, ProviderResult][] =
    results instanceof Map
      ? [...results.entries()]
      : results.map((r) => [r.provider, r] as [string, ProviderResult]);

  const eligibleCount = entries.filter(
    ([, r]) => r.success && typeof r.response === "string" && r.provider !== "Google Search",
  ).length;

  // Auto-trigger comparison when 2+ eligible results are available
  useEffect(() => {
    if (eligibleCount >= 2 && status === "idle" && !autoTriggered.current) {
      autoTriggered.current = true;
      generate(query, results);
    }
  }, [eligibleCount, status, query, results, generate]);

  if (eligibleCount < 2) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span>Cross-Provider Comparison</span>
          <div className="flex items-center gap-2">
            {status === "complete" && comparison && (
              <Badge variant="outline" className="text-xs font-normal">
                {comparison.model_used}
              </Badge>
            )}
            {status === "error" && (
              <Button size="sm" onClick={() => generate(query, results)}>
                Retry
              </Button>
            )}
            {status === "complete" && (
              <Button variant="ghost" size="sm" onClick={() => { reset(); autoTriggered.current = false; generate(query, results); }}>
                Regenerate
              </Button>
            )}
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent>
        {status === "loading" && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground animate-pulse">
              Claude Opus is analyzing key differences across {eligibleCount} providers...
            </p>
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {error || "Comparison failed"}
          </div>
        )}

        {status === "complete" && comparison && (
          <Tabs defaultValue="summary">
            <TabsList>
              <TabsTrigger value="summary">AI Summary</TabsTrigger>
              <TabsTrigger value="matrix">Claims Matrix</TabsTrigger>
              <TabsTrigger value="diff">Pick-Two Diff</TabsTrigger>
            </TabsList>
            <TabsContent value="summary" className="mt-4">
              <ComparisonSummary comparison={comparison} />
            </TabsContent>
            <TabsContent value="matrix" className="mt-4">
              <ClaimsMatrix claims={comparison.claims} rankings={comparison.provider_rankings} />
            </TabsContent>
            <TabsContent value="diff" className="mt-4">
              <DiffView
                claims={comparison.claims}
                providers={Object.keys(comparison.provider_rankings)}
              />
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
