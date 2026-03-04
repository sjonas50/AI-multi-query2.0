"use client";

import { useState } from "react";
import { SearchBar } from "@/components/search/SearchBar";
import { ConsensusAnswer } from "@/components/results/ConsensusAnswer";
import { ComparisonGrid } from "@/components/results/ComparisonGrid";
import { useQueryExecution } from "@/hooks/useQueryExecution";
import { useQueryHistory } from "@/hooks/useQueryHistory";
import { useAppModeContext } from "@/components/layout/AppModeProvider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exportAsJSON, exportAsCSV } from "@/lib/export";
import { useSavedSearches } from "@/hooks/useSavedSearches";
import type { ProviderResult } from "@/lib/types";

export default function SearchPage() {
  const { aiseoMode } = useAppModeContext();
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
  const { items: pinnedSearches } = useSavedSearches({ pinned: true });
  const [query, setQuery] = useState("");

  const hasResults = results.size > 0 || activeProviders.size > 0;
  const isIdle = status === "idle";
  const isDone = status === "complete" || status === "cancelled";

  const handleSubmit = (options: {
    providers: string[];
    analyze: boolean;
    request_sources: boolean;
    web_search: boolean | null;
    deep_research: boolean | null;
  }) => {
    if (!query.trim()) return;
    addEntry(query, options.providers);
    execute(query, options.providers, {
      analyze: options.analyze,
      request_sources: options.request_sources,
      web_search: options.web_search,
      deep_research: options.deep_research,
    });
  };

  const handleNewSearch = () => {
    setQuery("");
    reset();
  };

  const resultsArray: ProviderResult[] = [...results.values()];

  return (
    <div className={hasResults ? "space-y-6" : "flex min-h-[80vh] flex-col items-center justify-center"}>
      {/* Title — only when idle */}
      {!hasResults && (
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold tracking-tight">AI Search</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Compare answers from multiple AI models
          </p>
        </div>
      )}

      {/* Search bar */}
      <div className={hasResults ? "" : ""}>
        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={handleSubmit}
          onCancel={cancel}
          isRunning={status === "running"}
          compact={hasResults}
        />
      </div>

      {/* Pinned searches — only when idle */}
      {isIdle && pinnedSearches.length > 0 && (
        <div className="mt-6 w-full max-w-2xl mx-auto">
          <span className="text-xs font-medium text-muted-foreground mb-2 block">Pinned</span>
          <div className="flex flex-wrap gap-2">
            {pinnedSearches.slice(0, 6).map((item) => (
              <button
                key={item.id}
                onClick={() => setQuery(item.query)}
                className="rounded-full border border-yellow-300 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950 px-3 py-1 text-xs hover:bg-yellow-100 dark:hover:bg-yellow-900 transition-colors truncate max-w-[250px]"
              >
                {item.query}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Recent searches — only when idle */}
      {isIdle && history.length > 0 && (
        <div className="mt-6 w-full max-w-2xl mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-muted-foreground">Recent</span>
            <button
              onClick={clearHistory}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Clear
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {history.slice(0, 8).map((entry, i) => (
              <button
                key={i}
                onClick={() => setQuery(entry.query)}
                className="rounded-full border bg-background px-3 py-1 text-xs hover:bg-muted transition-colors truncate max-w-[250px]"
              >
                {entry.query}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Status messages */}
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
          Search cancelled.
        </div>
      )}

      {/* Completion bar */}
      {isDone && (
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {savedFilename && (
            <>
              <Badge variant="outline">Saved</Badge>
              <span className="text-xs">results/{savedFilename}</span>
            </>
          )}
          <div className="flex gap-1 ml-auto">
            <Button variant="ghost" size="sm" onClick={() => exportAsJSON(query, resultsArray)}>
              Export JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={() => exportAsCSV(query, resultsArray)}>
              Export CSV
            </Button>
            <Button variant="outline" size="sm" onClick={handleNewSearch}>
              New Search
            </Button>
          </div>
        </div>
      )}

      {/* Consensus answer — only in general search mode */}
      {!aiseoMode && hasResults && (
        <ConsensusAnswer results={results} activeProviders={activeProviders} />
      )}

      {/* Provider results */}
      {hasResults && (
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              {aiseoMode ? "Provider Responses" : "All Providers"}
            </span>
          </div>
          <ComparisonGrid
            results={results}
            activeProviders={activeProviders}
            retryingProviders={retryingProviders}
          />
        </div>
      )}
    </div>
  );
}
