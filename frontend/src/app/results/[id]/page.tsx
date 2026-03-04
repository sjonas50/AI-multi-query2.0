"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ComparisonGrid } from "@/components/results/ComparisonGrid";
import { ComparisonPanel } from "@/components/results/ComparisonPanel";
import { useComparison } from "@/hooks/useComparison";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exportAsJSON, exportAsCSV } from "@/lib/export";
import { useIsSaved } from "@/hooks/useSavedSearches";
import type { QueryResultData, ProviderResult, SavedSearch } from "@/lib/types";

interface BatchData {
  batch_timestamp: string;
  total_queries: number;
  queries_run: string[];
  all_results: Array<{ query: string; results: ProviderResult[] }>;
}

export default function ResultDetailPage() {
  const params = useParams();
  const filename = decodeURIComponent(params.id as string);
  const [data, setData] = useState<QueryResultData | BatchData | null>(null);
  const [loading, setLoading] = useState(true);
  const { savedId, refresh: refreshSaved } = useIsSaved(filename);
  const {
    comparison,
    status: comparisonStatus,
    error: comparisonError,
    generate: generateComparison,
    reset: resetComparison,
  } = useComparison();
  const [pinned, setPinned] = useState(false);

  useEffect(() => {
    api
      .get<QueryResultData | BatchData>(`/api/results/${encodeURIComponent(filename)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [filename]);

  // Fetch pin status when savedId changes
  useEffect(() => {
    if (savedId) {
      api
        .get<{ items: SavedSearch[] }>("/api/collections")
        .then((res) => {
          const match = res.items.find((i) => i.id === savedId);
          if (match) setPinned(match.pinned);
        })
        .catch(() => {});
    } else {
      setPinned(false);
    }
  }, [savedId]);

  const queryText = data
    ? "query" in data
      ? (data as QueryResultData).query
      : "Batch query"
    : "";

  const handleSave = useCallback(async () => {
    if (savedId) {
      await api.delete(`/api/collections/${savedId}`);
    } else {
      await api.post<SavedSearch>("/api/collections", {
        result_filename: filename,
        query: queryText,
      });
    }
    refreshSaved();
  }, [savedId, filename, queryText, refreshSaved]);

  const handlePin = useCallback(async () => {
    if (savedId) {
      await api.put<SavedSearch>(`/api/collections/${savedId}`, {
        pinned: !pinned,
      });
      setPinned(!pinned);
    } else {
      // Save first then pin
      const item = await api.post<SavedSearch>("/api/collections", {
        result_filename: filename,
        query: queryText,
        pinned: true,
      });
      setPinned(true);
      refreshSaved();
    }
  }, [savedId, pinned, filename, queryText, refreshSaved]);

  if (loading) {
    return <div className="text-muted-foreground">Loading...</div>;
  }

  if (!data) {
    return <div className="text-red-600">Result not found.</div>;
  }

  const isBatch = "all_results" in data;

  if (isBatch) {
    const batch = data as BatchData;
    return (
      <div className="space-y-8">
        <div>
          <h2 className="text-2xl font-bold">Batch Results</h2>
          <p className="text-sm text-muted-foreground">
            {batch.total_queries} queries &middot;{" "}
            {new Date(batch.batch_timestamp).toLocaleString()}
          </p>
        </div>
        {batch.all_results.map((entry, i) => (
          <div key={i} className="space-y-3">
            <h3 className="text-lg font-semibold">{entry.query}</h3>
            <ComparisonGrid results={entry.results} />
          </div>
        ))}
      </div>
    );
  }

  const result = data as QueryResultData;
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold">{result.query}</h2>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>{result.date}</span>
            <span>{result.time}</span>
            <Badge variant="outline">{result.results.length} providers</Badge>
          </div>
        </div>
        <div className="flex gap-1">
          <Button
            variant={pinned ? "default" : "ghost"}
            size="sm"
            onClick={handlePin}
            title={pinned ? "Unpin" : "Pin"}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={pinned ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
              <path d="M12 17.75l-6.172 3.245l1.179 -6.873l-5 -4.867l6.9 -1l3.086 -6.253l3.086 6.253l6.9 1l-5 4.867l1.179 6.873z" />
            </svg>
            {pinned ? "Pinned" : "Pin"}
          </Button>
          <Button
            variant={savedId ? "default" : "ghost"}
            size="sm"
            onClick={handleSave}
            title={savedId ? "Unsave" : "Save"}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={savedId ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
              <path d="M19 21l-7 -4l-7 4V5a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2z" />
            </svg>
            {savedId ? "Saved" : "Save"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => exportAsJSON(result.query, result.results, comparison, filename.replace(".json", "_export.json"))}
          >
            Export JSON
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => exportAsCSV(result.query, result.results, comparison, filename.replace(".json", "_export.csv"))}
          >
            Export CSV
          </Button>
        </div>
      </div>
      <ComparisonGrid results={result.results} />
      <ComparisonPanel
        query={result.query}
        results={result.results}
        comparison={comparison}
        comparisonStatus={comparisonStatus}
        comparisonError={comparisonError}
        onGenerate={generateComparison}
        onReset={resetComparison}
      />
    </div>
  );
}
