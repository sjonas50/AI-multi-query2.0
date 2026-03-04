"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { ProviderResult, ComparisonResult } from "@/lib/types";

type ComparisonStatus = "idle" | "loading" | "complete" | "error";

export function useComparison() {
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [status, setStatus] = useState<ComparisonStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(
    async (query: string, results: Map<string, ProviderResult> | ProviderResult[]) => {
      const responses: Record<string, string> = {};
      const entries: Iterable<[string, ProviderResult]> =
        results instanceof Map
          ? results.entries()
          : results.map((r) => [r.provider, r] as [string, ProviderResult]);

      for (const [, result] of entries) {
        if (result.success && typeof result.response === "string" && result.provider !== "Google Search") {
          responses[result.provider] = result.response;
        }
      }

      if (Object.keys(responses).length < 2) {
        const allProviders = [...(results instanceof Map ? results.values() : results)];
        const detail = allProviders
          .map((r) => `${r.provider}: success=${r.success}, type=${typeof r.response}`)
          .join("; ");
        setError(`Need at least 2 successful LLM responses to compare (found ${Object.keys(responses).length}). Providers: ${detail}`);
        setStatus("error");
        return;
      }

      setStatus("loading");
      setError(null);

      try {
        const data = await api.post<ComparisonResult>("/api/comparisons", { query, responses });
        setComparison(data);
        setStatus("complete");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Comparison failed");
        setStatus("error");
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setComparison(null);
    setStatus("idle");
    setError(null);
  }, []);

  return { comparison, status, error, generate, reset };
}
