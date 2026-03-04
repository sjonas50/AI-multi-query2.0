"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SavedSearch } from "@/lib/types";

interface ListResponse {
  items: SavedSearch[];
}

export function useSavedSearches(opts?: { tag?: string; pinned?: boolean }) {
  const [items, setItems] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    const params = new URLSearchParams();
    if (opts?.tag) params.set("tag", opts.tag);
    if (opts?.pinned) params.set("pinned", "true");
    const qs = params.toString();
    api
      .get<ListResponse>(`/api/collections${qs ? `?${qs}` : ""}`)
      .then((res) => setItems(res.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [opts?.tag, opts?.pinned]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const save = useCallback(
    async (result_filename: string, query: string, tags: string[] = []) => {
      const item = await api.post<SavedSearch>("/api/collections", {
        result_filename,
        query,
        tags,
      });
      refresh();
      return item;
    },
    [refresh],
  );

  const unsave = useCallback(
    async (id: string) => {
      await api.delete("/api/collections/" + id);
      refresh();
    },
    [refresh],
  );

  const togglePin = useCallback(
    async (id: string, currentPinned: boolean) => {
      await api.put<SavedSearch>(`/api/collections/${id}`, {
        pinned: !currentPinned,
      });
      refresh();
    },
    [refresh],
  );

  const updateTags = useCallback(
    async (id: string, tags: string[]) => {
      await api.put<SavedSearch>(`/api/collections/${id}`, { tags });
      refresh();
    },
    [refresh],
  );

  return { items, loading, refresh, save, unsave, togglePin, updateTags };
}

/** Check if a single filename is saved. Returns the saved search id or null. */
export function useIsSaved(result_filename: string) {
  const [savedId, setSavedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const check = useCallback(() => {
    api
      .get<ListResponse>("/api/collections")
      .then((res) => {
        const match = res.items.find(
          (i) => i.result_filename === result_filename,
        );
        setSavedId(match?.id ?? null);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [result_filename]);

  useEffect(() => {
    check();
  }, [check]);

  return { savedId, loading, refresh: check };
}
