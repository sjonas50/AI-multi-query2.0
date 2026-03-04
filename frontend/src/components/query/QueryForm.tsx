"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useAppModeContext } from "@/components/layout/AppModeProvider";
import type { ProviderInfo } from "@/lib/types";
import type { HistoryEntry } from "@/hooks/useQueryHistory";

interface QueryOptions {
  analyze: boolean;
  request_sources: boolean;
  web_search: boolean | null;
  deep_research: boolean | null;
}

interface QueryFormProps {
  onSubmit: (query: string, providers: string[], options: QueryOptions) => void;
  onCancel?: () => void;
  isRunning: boolean;
  isCancellable?: boolean;
  history?: HistoryEntry[];
  onClearHistory?: () => void;
}

export function QueryForm({
  onSubmit,
  onCancel,
  isRunning,
  isCancellable,
  history = [],
  onClearHistory,
}: QueryFormProps) {
  const { aiseoMode } = useAppModeContext();
  const [query, setQuery] = useState("");
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [analyze, setAnalyze] = useState(false);
  const [requestSources, setRequestSources] = useState(false);
  const [webSearch, setWebSearch] = useState<boolean | null>(null);
  const [deepResearch, setDeepResearch] = useState<boolean | null>(null);
  const [batchMode, setBatchMode] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get<{ providers: ProviderInfo[] }>("/api/providers").then(({ providers: p }) => {
      setProviders(p);
      setSelected(new Set(p.filter((pr) => pr.configured).map((pr) => pr.id)));
    });
  }, []);

  // Close history dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (historyRef.current && !historyRef.current.contains(e.target as Node)) {
        setShowHistory(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const toggleProvider = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedProviders = providers.filter((p) => selected.has(p.id));
  const anyWebSearchSupported = selectedProviders.some((p) => p.web_search_supported);
  const anyDeepResearchSupported = selectedProviders.some((p) => p.deep_research_supported);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isRunning) return;
    onSubmit(query.trim(), [...selected], {
      analyze,
      request_sources: requestSources,
      web_search: webSearch,
      deep_research: deepResearch,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (!query.trim() || isRunning || selected.size === 0) return;
      onSubmit(query.trim(), [...selected], {
        analyze,
        request_sources: requestSources,
        web_search: webSearch,
        deep_research: deepResearch,
      });
    }
  };

  const selectHistoryEntry = (entry: HistoryEntry) => {
    setQuery(entry.query);
    setShowHistory(false);
    textareaRef.current?.focus();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <div className="flex items-center justify-between">
          <Label htmlFor="query">{batchMode ? "Queries (one per line)" : "Query"}</Label>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <div ref={historyRef} className="relative">
                <button
                  type="button"
                  onClick={() => setShowHistory(!showHistory)}
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  Recent ({history.length})
                </button>
                {showHistory && (
                  <div className="absolute right-0 top-6 z-50 w-80 rounded-md border bg-popover p-1 shadow-lg">
                    <div className="max-h-60 overflow-y-auto">
                      {history.map((entry, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => selectHistoryEntry(entry)}
                          className="block w-full rounded px-2 py-1.5 text-left text-sm hover:bg-muted truncate"
                        >
                          {entry.query}
                        </button>
                      ))}
                    </div>
                    {onClearHistory && (
                      <button
                        type="button"
                        onClick={() => { onClearHistory(); setShowHistory(false); }}
                        className="mt-1 block w-full rounded px-2 py-1 text-center text-xs text-muted-foreground hover:bg-muted"
                      >
                        Clear history
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
            <label className="flex items-center gap-1 text-xs text-muted-foreground">
              <input
                type="checkbox"
                checked={batchMode}
                onChange={(e) => setBatchMode(e.target.checked)}
                disabled={isRunning}
                className="rounded"
              />
              Batch
            </label>
          </div>
        </div>
        <Textarea
          ref={textareaRef}
          id="query"
          placeholder={batchMode ? "Enter one query per line..." : "Enter your question... (Cmd+Enter to submit)"}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="mt-1 min-h-[80px]"
          disabled={isRunning}
          rows={batchMode ? 6 : 3}
        />
      </div>

      <div>
        <Label>Providers</Label>
        <div className="mt-1 flex flex-wrap gap-2">
          {providers.map((p) => (
            <button
              key={p.id}
              type="button"
              disabled={!p.configured || isRunning}
              onClick={() => toggleProvider(p.id)}
              className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
                selected.has(p.id)
                  ? "border-primary bg-primary text-primary-foreground"
                  : p.configured
                    ? "border-input bg-background hover:bg-muted"
                    : "border-muted bg-muted/50 text-muted-foreground opacity-50"
              }`}
            >
              {p.name}
              {p.model && <span className="ml-1 text-xs opacity-70">({p.model})</span>}
            </button>
          ))}
        </div>
      </div>

      {aiseoMode && (
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={analyze}
              onChange={(e) => setAnalyze(e.target.checked)}
              disabled={isRunning}
              className="rounded"
            />
            Run AISEO analysis
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={requestSources}
              onChange={(e) => setRequestSources(e.target.checked)}
              disabled={isRunning}
              className="rounded"
            />
            Request sources
          </label>
        </div>
      )}

      {(anyWebSearchSupported || anyDeepResearchSupported) && (
        <div className="rounded-md border p-3 space-y-3">
          <Label className="text-sm font-medium">Search Options</Label>
          <div className="flex flex-wrap items-center gap-4">
            {anyWebSearchSupported && (
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={webSearch === true}
                  onChange={(e) => setWebSearch(e.target.checked ? true : null)}
                  disabled={isRunning}
                  className="rounded"
                />
                <span>Web Search</span>
                <span className="text-xs text-muted-foreground">
                  ({selectedProviders.filter((p) => p.web_search_supported).map((p) => p.name).join(", ")})
                </span>
              </label>
            )}
            {anyDeepResearchSupported && (
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={deepResearch === true}
                  onChange={(e) => setDeepResearch(e.target.checked ? true : null)}
                  disabled={isRunning}
                  className="rounded"
                />
                <span>Deep Research</span>
                <span className="text-xs text-muted-foreground">
                  ({selectedProviders.filter((p) => p.deep_research_supported).map((p) => p.name).join(", ")})
                </span>
              </label>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            When unchecked, per-provider defaults from .env are used. Check to force enable for all supported providers.
          </p>
        </div>
      )}

      <div className="flex items-center gap-2">
        <Button type="submit" disabled={!query.trim() || selected.size === 0 || isRunning}>
          {isRunning ? "Running..." : batchMode ? "Execute Batch" : "Execute Query"}
        </Button>
        {isRunning && isCancellable && onCancel && (
          <Button type="button" variant="destructive" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <span className="text-xs text-muted-foreground hidden sm:inline">
          {navigator.platform?.includes("Mac") ? "Cmd" : "Ctrl"}+Enter to submit
        </span>
      </div>
    </form>
  );
}
