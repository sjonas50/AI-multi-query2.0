"use client";

import { ProviderCard } from "./ProviderCard";
import type { ProviderResult } from "@/lib/types";

interface ComparisonGridProps {
  results: Map<string, ProviderResult> | ProviderResult[];
  activeProviders?: Set<string>;
  retryingProviders?: Map<string, number>;
}

export function ComparisonGrid({
  results,
  activeProviders = new Set(),
  retryingProviders = new Map(),
}: ComparisonGridProps) {
  const resultMap: Map<string, ProviderResult> =
    results instanceof Map
      ? results
      : new Map(results.map((r) => [r.provider, r]));

  const allProviders = new Set([...activeProviders, ...resultMap.keys()]);

  if (allProviders.size === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {[...allProviders].map((provider) => (
        <ProviderCard
          key={provider}
          provider={provider}
          result={resultMap.get(provider)}
          isLoading={activeProviders.has(provider)}
          retryAttempt={retryingProviders.get(provider)}
        />
      ))}
    </div>
  );
}
