"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ResultListItem, ProviderInfo } from "@/lib/types";

export default function DashboardPage() {
  const [results, setResults] = useState<ResultListItem[]>([]);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [totalResults, setTotalResults] = useState(0);

  useEffect(() => {
    api
      .get<{ items: ResultListItem[]; total: number }>("/api/results?limit=5")
      .then((d) => {
        setResults(d.items);
        setTotalResults(d.total);
      });
    api
      .get<{ providers: ProviderInfo[] }>("/api/providers")
      .then((d) => setProviders(d.providers));
  }, []);

  const configuredCount = providers.filter((p) => p.configured).length;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalResults}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Configured Providers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {configuredCount}/{providers.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Link
              href="/query"
              className="inline-block rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90"
            >
              New Query
            </Link>
          </CardContent>
        </Card>
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Recent Results</h3>
          <Link href="/results" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
            View all
          </Link>
        </div>
        <div className="space-y-2">
          {results.map((item) => (
            <Link
              key={item.filename}
              href={`/results/${encodeURIComponent(item.filename)}`}
              className="flex items-center justify-between rounded-md border p-3 hover:bg-muted/30"
            >
              <div className="flex items-center gap-2">
                <span className="line-clamp-1 text-sm">{item.query}</span>
                {item.is_batch && (
                  <Badge variant="secondary" className="text-xs">
                    Batch
                  </Badge>
                )}
              </div>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {item.timestamp ? new Date(item.timestamp).toLocaleDateString() : "—"}
              </span>
            </Link>
          ))}
          {results.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No results yet.{" "}
              <Link href="/query" className="text-blue-600 hover:underline">
                Run your first query
              </Link>
            </p>
          )}
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-lg font-semibold">Providers</h3>
        <div className="flex flex-wrap gap-2">
          {providers.map((p) => (
            <Badge
              key={p.id}
              variant={p.configured ? "default" : "outline"}
              className="text-sm"
            >
              {p.name}
              {p.model && <span className="ml-1 opacity-70">({p.model})</span>}
              {!p.configured && <span className="ml-1 opacity-50">Not configured</span>}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
