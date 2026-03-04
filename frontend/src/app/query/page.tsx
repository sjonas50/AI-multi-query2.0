"use client";

import { useState, useRef, useEffect } from "react";
import { QueryForm } from "@/components/query/QueryForm";
import { FollowUpInput } from "@/components/query/FollowUpInput";
import { SuggestedQuestions } from "@/components/query/SuggestedQuestions";
import { ComparisonGrid } from "@/components/results/ComparisonGrid";
import { ComparisonPanel } from "@/components/results/ComparisonPanel";
import { useQueryExecution } from "@/hooks/useQueryExecution";
import { useComparison } from "@/hooks/useComparison";
import { useQueryHistory } from "@/hooks/useQueryHistory";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exportAsJSON, exportAsCSV } from "@/lib/export";
import type { ProviderResult } from "@/lib/types";

interface ConversationTurn {
  query: string;
  results: ProviderResult[];
  savedFilename?: string | null;
}

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
    conversationId,
    suggestions,
    suggestionsLoading,
  } = useQueryExecution();
  const {
    comparison,
    status: comparisonStatus,
    error: comparisonError,
    generate: generateComparison,
    reset: resetComparison,
  } = useComparison();
  const { history, addEntry, clearHistory } = useQueryHistory();
  const [currentQuery, setCurrentQuery] = useState("");
  const [pastTurns, setPastTurns] = useState<ConversationTurn[]>([]);
  const [lastProviders, setLastProviders] = useState<string[]>([]);
  const [lastOptions, setLastOptions] = useState<{
    analyze: boolean;
    request_sources: boolean;
    web_search: boolean | null;
    deep_research: boolean | null;
  }>({ analyze: false, request_sources: false, web_search: null, deep_research: null });
  const bottomRef = useRef<HTMLDivElement>(null);

  // Save current turn to history when a new follow-up starts
  const saveTurn = () => {
    if (currentQuery && results.size > 0) {
      setPastTurns((prev) => [
        ...prev,
        {
          query: currentQuery,
          results: [...results.values()],
          savedFilename,
        },
      ]);
    }
  };

  // Auto-scroll to bottom when new results come in
  useEffect(() => {
    if (status === "running" || status === "complete") {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [status, results.size]);

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
    setLastProviders(providers);
    setLastOptions(options);
    resetComparison();

    const lines = query.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length > 1) {
      setCurrentQuery(lines[0]);
      execute(lines[0], providers, options);
    } else {
      setCurrentQuery(query);
      execute(query, providers, options);
    }
  };

  const handleFollowUp = (query: string) => {
    saveTurn();
    setCurrentQuery(query);
    resetComparison();
    execute(query, lastProviders, {
      ...lastOptions,
      conversation_id: conversationId,
    });
  };

  const handleReset = () => {
    setPastTurns([]);
    setCurrentQuery("");
    reset();
    resetComparison();
  };

  const resultsArray: ProviderResult[] = [...results.values()];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          {pastTurns.length > 0 ? "Conversation" : "New Query"}
        </h2>
        {(status === "complete" || status === "cancelled") && (
          <Button variant="outline" size="sm" onClick={handleReset}>
            New Query
          </Button>
        )}
      </div>

      {pastTurns.length === 0 && (
        <QueryForm
          onSubmit={handleSubmit}
          onCancel={cancel}
          isRunning={status === "running"}
          isCancellable={status === "running"}
          history={history}
          onClearHistory={clearHistory}
        />
      )}

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

      {/* Past conversation turns */}
      {pastTurns.map((turn, i) => (
        <div key={i} className="space-y-3 border-b pb-6">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">Turn {i + 1}</Badge>
            <h3 className="text-sm font-medium">{turn.query}</h3>
          </div>
          <ComparisonGrid results={turn.results} />
        </div>
      ))}

      {/* Current turn */}
      {(pastTurns.length > 0 && (results.size > 0 || activeProviders.size > 0)) && (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">Turn {pastTurns.length + 1}</Badge>
          <h3 className="text-sm font-medium">{currentQuery}</h3>
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
            <Button variant="ghost" size="sm" onClick={() => exportAsJSON(currentQuery, resultsArray, comparison)}>
              Export JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={() => exportAsCSV(currentQuery, resultsArray, comparison)}>
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

      {status === "complete" && currentQuery && (
        <ComparisonPanel
          query={currentQuery}
          results={results}
          comparison={comparison}
          comparisonStatus={comparisonStatus}
          comparisonError={comparisonError}
          onGenerate={generateComparison}
          onReset={resetComparison}
        />
      )}

      {/* Suggested follow-up questions */}
      {status === "complete" && (
        <SuggestedQuestions
          questions={suggestions}
          loading={suggestionsLoading}
          onSelect={handleFollowUp}
        />
      )}

      {/* Follow-up input */}
      {status === "complete" && (
        <FollowUpInput onSubmit={handleFollowUp} disabled={status !== "complete"} />
      )}

      <div ref={bottomRef} />
    </div>
  );
}
