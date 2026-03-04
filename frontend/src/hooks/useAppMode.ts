"use client";

import { useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "app_mode";

export type AppMode = "search" | "aiseo";

export function useAppMode() {
  const [mode, setMode] = useState<AppMode>("search");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "aiseo") setMode("aiseo");
    } catch {
      // ignore
    }
  }, []);

  const toggleAiseoMode = useCallback(() => {
    setMode((prev) => {
      const next = prev === "search" ? "aiseo" : "search";
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  const setAiseoMode = useCallback((on: boolean) => {
    const next = on ? "aiseo" : "search";
    setMode(next);
    localStorage.setItem(STORAGE_KEY, next);
  }, []);

  return {
    aiseoMode: mode === "aiseo",
    mode,
    toggleAiseoMode,
    setAiseoMode,
  };
}
