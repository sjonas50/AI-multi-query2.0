"use client";

import { useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "query_history";
const MAX_HISTORY = 50;

export interface HistoryEntry {
  query: string;
  timestamp: string;
  providers: string[];
}

export function useQueryHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setHistory(JSON.parse(stored));
    } catch {
      // ignore corrupt storage
    }
  }, []);

  const addEntry = useCallback((query: string, providers: string[]) => {
    setHistory((prev) => {
      // Deduplicate: remove if same query exists
      const filtered = prev.filter((e) => e.query !== query);
      const next = [
        { query, timestamp: new Date().toISOString(), providers },
        ...filtered,
      ].slice(0, MAX_HISTORY);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return { history, addEntry, clearHistory };
}
