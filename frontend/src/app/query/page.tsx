"use client";

import { QueryForm } from "@/components/query/QueryForm";
import { ComparisonGrid } from "@/components/results/ComparisonGrid";
import { useQueryExecution } from "@/hooks/useQueryExecution";
import { useQueryHistory } from "@/hooks/useQueryHistory";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exportAsJSON, exportAsCSV } from "@/lib/export";
import type { ProviderResult } from "@/lib/types";

export default function QueryPage() {
  const {
    execute,
    cancel,
    reset,
    results,
    activeProviders,
    retryingProviders,
    status,
    error,
    savedFilename,
    reconnecting,
  } = useQueryExecution();
  const { history, addEntry, clearHistory } = useQueryHistory();

  const handleSubmit = (
    query: string,
    providers: string[],
    options: {
      analyze: boolean;
      request_sources: boolean;
      web_search: boolean | null;
      deep_research: boolean | null;
    },
  ) => {
    addEntry(query, providers);

    // Check for batch mode: multiple lines = multiple queries
    const lines = query.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length > 1) {
      // For batch, run first query. Batch sequencing is handled by running one at a time.
      // Future: implement full batch with progress tracking
      execute(lines[0], providers, options);
    } else {
      execute(query, providers, options);
    }
  };

  const resultsArray: ProviderResult[] = [...results.values()];

  const handleExportJSON = () => {
    exportAsJSON("query", resultsArray);
  };

  const handleExportCSV = () => {
    exportAsCSV("query", resultsArray);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">New Query</h2>
        {(status === "complete" || status === "cancelled") && (
          <Button variant="outline" size="sm" onClick={reset}>
            New Query
          </Button>
        )}
      </div>

      <QueryForm
        onSubmit={handleSubmit}
        onCancel={cancel}
        isRunning={status === "running"}
        isCancellable={status === "running"}
        history={history}
        onClearHistory={clearHistory}
      />

      {reconnecting && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-700 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-300">
          Reconnecting to server...
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {status === "cancelled" && (
        <div className="rounded-md border border-orange-300 bg-orange-50 p-3 text-sm text-orange-700 dark:border-orange-800 dark:bg-orange-950 dark:text-orange-300">
          Query cancelled.
        </div>
      )}

      {status === "complete" && (
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {savedFilename && (
            <>
              <Badge variant="outline">Saved</Badge>
              <span>results/{savedFilename}</span>
            </>
          )}
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={handleExportJSON}>
              Export JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={handleExportCSV}>
              Export CSV
            </Button>
          </div>
        </div>
      )}

      {(results.size > 0 || activeProviders.size > 0) && (
        <ComparisonGrid
          results={results}
          activeProviders={activeProviders}
          retryingProviders={retryingProviders}
        />
      )}
    </div>
  );
}
