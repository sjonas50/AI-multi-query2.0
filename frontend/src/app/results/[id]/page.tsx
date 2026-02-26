"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ComparisonGrid } from "@/components/results/ComparisonGrid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exportAsJSON, exportAsCSV } from "@/lib/export";
import type { QueryResultData, ProviderResult } from "@/lib/types";

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

  useEffect(() => {
    api
      .get<QueryResultData | BatchData>(`/api/results/${encodeURIComponent(filename)}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [filename]);

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
            variant="ghost"
            size="sm"
            onClick={() => exportAsJSON(result.query, result.results, filename.replace(".json", "_export.json"))}
          >
            Export JSON
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => exportAsCSV(result.query, result.results, filename.replace(".json", "_export.csv"))}
          >
            Export CSV
          </Button>
        </div>
      </div>
      <ComparisonGrid results={result.results} />
    </div>
  );
}
