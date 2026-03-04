"use client";

import { createContext, useContext } from "react";
import { useAppMode } from "@/hooks/useAppMode";

interface AppModeContextValue {
  aiseoMode: boolean;
  toggleAiseoMode: () => void;
  setAiseoMode: (on: boolean) => void;
}

const AppModeContext = createContext<AppModeContextValue>({
  aiseoMode: false,
  toggleAiseoMode: () => {},
  setAiseoMode: () => {},
});

export function AppModeProvider({ children }: { children: React.ReactNode }) {
  const { aiseoMode, toggleAiseoMode, setAiseoMode } = useAppMode();

  return (
    <AppModeContext.Provider value={{ aiseoMode, toggleAiseoMode, setAiseoMode }}>
      {children}
    </AppModeContext.Provider>
  );
}

export function useAppModeContext() {
  return useContext(AppModeContext);
}
