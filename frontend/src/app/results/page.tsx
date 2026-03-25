"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useSavedSearches } from "@/hooks/useSavedSearches";
import type { ResultListItem } from "@/lib/types";

interface PaginatedResponse {
  items: ResultListItem[];
  total: number;
  page: number;
  limit: number;
}

type FilterTab = "all" | "saved";

export default function ResultsPage() {
  const [data, setData] = useState<PaginatedResponse | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [tab, setTab] = useState<FilterTab>("all");
  const limit = 20;

  const { items: savedItems, save, unsave, togglePin, refresh: refreshSaved } = useSavedSearches();

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (search) params.set("search", search);
    api.get<PaginatedResponse>(`/api/results?${params}`).then(setData);
  }, [page, search]);

  const savedFilenames = new Set(savedItems.map((s) => s.result_filename));
  const savedMap = new Map(savedItems.map((s) => [s.result_filename, s]));

  const displayItems =
    tab === "saved"
      ? (data?.items ?? []).filter((item) => savedFilenames.has(item.filename))
      : (data?.items ?? []);

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  const handleSaveToggle = async (item: ResultListItem) => {
    const existing = savedMap.get(item.filename);
    if (existing) {
      await unsave(existing.id);
    } else {
      await save(item.filename, item.query);
    }
  };

  const handlePinToggle = async (item: ResultListItem) => {
    const existing = savedMap.get(item.filename);
    if (existing) {
      await togglePin(existing.id, existing.pinned);
    } else {
      // Save first, then it will be pinned on next action
      await save(item.filename, item.query);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">History</h2>
        <span className="text-sm text-muted-foreground">
          {data?.total ?? 0} total results
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex rounded-md border">
          <button
            onClick={() => { setTab("all"); setPage(1); }}
            className={`px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === "all"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
          >
            All
          </button>
          <button
            onClick={() => { setTab("saved"); setPage(1); }}
            className={`px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === "saved"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            }`}
          >
            Saved ({savedItems.length})
          </button>
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
      </div>

      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-2 text-left font-medium">Query</th>
              <th className="px-4 py-2 text-left font-medium">Date</th>
              <th className="px-4 py-2 text-left font-medium">Providers</th>
              <th className="px-4 py-2 text-left font-medium">Analysis</th>
              <th className="px-4 py-2 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {displayItems.map((item) => {
              const saved = savedMap.get(item.filename);
              return (
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
                  <td className="px-4 py-2 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handlePinToggle(item)}
                        className={`p-1 rounded hover:bg-muted transition-colors ${
                          saved?.pinned
                            ? "text-yellow-500 dark:text-yellow-400"
                            : "text-muted-foreground"
                        }`}
                        title={saved?.pinned ? "Unpin" : "Pin"}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={saved?.pinned ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 17.75l-6.172 3.245l1.179 -6.873l-5 -4.867l6.9 -1l3.086 -6.253l3.086 6.253l6.9 1l-5 4.867l1.179 6.873z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleSaveToggle(item)}
                        className={`p-1 rounded hover:bg-muted transition-colors ${
                          saved
                            ? "text-blue-500 dark:text-blue-400"
                            : "text-muted-foreground"
                        }`}
                        title={saved ? "Unsave" : "Save"}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={saved ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M19 21l-7 -4l-7 4V5a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2z" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {displayItems.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  {tab === "saved" ? "No saved searches yet." : "No results found."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {tab === "all" && totalPages > 1 && (
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
