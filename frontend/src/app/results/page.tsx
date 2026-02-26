"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { ResultListItem } from "@/lib/types";

interface PaginatedResponse {
  items: ResultListItem[];
  total: number;
  page: number;
  limit: number;
}

export default function ResultsPage() {
  const [data, setData] = useState<PaginatedResponse | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const limit = 20;

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (search) params.set("search", search);
    api.get<PaginatedResponse>(`/api/results?${params}`).then(setData);
  }, [page, search]);

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Results</h2>
        <span className="text-sm text-muted-foreground">
          {data?.total ?? 0} total results
        </span>
      </div>

      <Input
        placeholder="Search queries..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
        className="max-w-sm"
      />

      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-2 text-left font-medium">Query</th>
              <th className="px-4 py-2 text-left font-medium">Date</th>
              <th className="px-4 py-2 text-left font-medium">Providers</th>
              <th className="px-4 py-2 text-left font-medium">Analysis</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((item) => (
              <tr key={item.filename} className="border-b hover:bg-muted/30">
                <td className="px-4 py-2">
                  <Link
                    href={`/results/${encodeURIComponent(item.filename)}`}
                    className="text-blue-600 hover:underline dark:text-blue-400"
                  >
                    <span className="line-clamp-1">{item.query}</span>
                  </Link>
                  {item.is_batch && (
                    <Badge variant="secondary" className="ml-2 text-xs">
                      Batch
                    </Badge>
                  )}
                </td>
                <td className="px-4 py-2 text-muted-foreground whitespace-nowrap">
                  {item.timestamp
                    ? new Date(item.timestamp).toLocaleDateString()
                    : "—"}
                </td>
                <td className="px-4 py-2">
                  <Badge variant="outline">{item.provider_count}</Badge>
                </td>
                <td className="px-4 py-2">
                  {item.has_analysis && (
                    <Badge variant="secondary" className="text-xs">
                      AISEO
                    </Badge>
                  )}
                </td>
              </tr>
            ))}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                  No results found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
