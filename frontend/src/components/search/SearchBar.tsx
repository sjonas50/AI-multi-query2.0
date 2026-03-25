"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { useAppModeContext } from "@/components/layout/AppModeProvider";
import type { ProviderInfo } from "@/lib/types";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (options: {
    providers: string[];
    analyze: boolean;
    request_sources: boolean;
    web_search: boolean | null;
    deep_research: boolean | null;
  }) => void;
  onCancel?: () => void;
  isRunning: boolean;
  compact?: boolean;
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  onCancel,
  isRunning,
  compact,
}: SearchBarProps) {
  const { aiseoMode } = useAppModeContext();
  const [showOptions, setShowOptions] = useState(false);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [analyze, setAnalyze] = useState(false);
  const [requestSources, setRequestSources] = useState(false);
  const [webSearch, setWebSearch] = useState<boolean | null>(null);
  const [deepResearch, setDeepResearch] = useState<boolean | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get<{ providers: ProviderInfo[] }>("/api/providers").then(({ providers: p }) => {
      setProviders(p);
      setSelected(new Set(p.filter((pr) => pr.configured).map((pr) => pr.id)));
    });
  }, []);

  useEffect(() => {
    if (!compact) inputRef.current?.focus();
  }, [compact]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!value.trim() || isRunning) return;
    onSubmit({
      providers: [...selected],
      analyze,
      request_sources: requestSources,
      web_search: webSearch,
      deep_research: deepResearch,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

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

  return (
    <div className={compact ? "w-full" : "w-full max-w-2xl mx-auto"}>
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <svg
            className="absolute left-3 h-5 w-5 text-muted-foreground pointer-events-none"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            disabled={isRunning}
            className={`w-full rounded-xl border bg-background pl-10 pr-24 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 ${
              compact ? "h-10" : "h-12"
            }`}
          />
          <div className="absolute right-2 flex items-center gap-1">
            {isRunning && onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="rounded-lg px-2 py-1 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950"
              >
                Cancel
              </button>
            )}
            <button
              type="button"
              onClick={() => setShowOptions(!showOptions)}
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              title="Options"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
            </button>
            {!isRunning && (
              <button
                type="submit"
                disabled={!value.trim() || selected.size === 0}
                className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50 hover:opacity-90"
              >
                Search
              </button>
            )}
          </div>
        </div>
      </form>

      {showOptions && (
        <div className="mt-2 rounded-xl border bg-background p-4 shadow-sm space-y-3">
          <div>
            <span className="text-xs font-medium text-muted-foreground">Providers</span>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {providers.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  disabled={!p.configured || isRunning}
                  onClick={() => toggleProvider(p.id)}
                  className={`rounded-md border px-2 py-1 text-xs transition-colors ${
                    selected.has(p.id)
                      ? "border-primary bg-primary text-primary-foreground"
                      : p.configured
                        ? "border-input bg-background hover:bg-muted"
                        : "border-muted bg-muted/50 text-muted-foreground opacity-50"
                  }`}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {(anyWebSearchSupported || anyDeepResearchSupported) && (
            <div className="flex flex-wrap gap-3">
              {anyWebSearchSupported && (
                <label className="flex items-center gap-1.5 text-xs">
                  <input
                    type="checkbox"
                    checked={webSearch === true}
                    onChange={(e) => setWebSearch(e.target.checked ? true : null)}
                    disabled={isRunning}
                    className="rounded"
                  />
                  Web Search
                </label>
              )}
              {anyDeepResearchSupported && (
                <label className="flex items-center gap-1.5 text-xs">
                  <input
                    type="checkbox"
                    checked={deepResearch === true}
                    onChange={(e) => setDeepResearch(e.target.checked ? true : null)}
                    disabled={isRunning}
                    className="rounded"
                  />
                  Deep Research
                </label>
              )}
            </div>
          )}

          {aiseoMode && (
            <div className="flex flex-wrap gap-3 border-t pt-3">
              <label className="flex items-center gap-1.5 text-xs">
                <input
                  type="checkbox"
                  checked={analyze}
                  onChange={(e) => setAnalyze(e.target.checked)}
                  disabled={isRunning}
                  className="rounded"
                />
                AISEO Analysis
              </label>
              <label className="flex items-center gap-1.5 text-xs">
                <input
                  type="checkbox"
                  checked={requestSources}
                  onChange={(e) => setRequestSources(e.target.checked)}
                  disabled={isRunning}
                  className="rounded"
                />
                Request Sources
              </label>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
