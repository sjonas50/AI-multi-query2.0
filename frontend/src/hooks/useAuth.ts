"use client";

import { createContext, useContext } from "react";
import type { User } from "@/lib/types";

export interface AuthContextType {
  isLoggedIn: boolean;
  user: User | null;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  isLoggedIn: false,
  user: null,
  isAdmin: false,
  login: async () => {},
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}
