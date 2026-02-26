"use client";

import { useState, useEffect, ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, setToken, clearToken, isAuthenticated } from "@/lib/api";
import { AuthContext } from "@/hooks/useAuth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    setIsLoggedIn(isAuthenticated());
    setChecking(false);
  }, []);

  useEffect(() => {
    if (!checking && !isLoggedIn && pathname !== "/login") {
      router.push("/login");
    }
  }, [checking, isLoggedIn, pathname, router]);

  const login = async (password: string) => {
    const { token } = await api.post<{ token: string }>("/api/auth/login", { password });
    setToken(token);
    setIsLoggedIn(true);
    router.push("/");
  };

  const logout = () => {
    clearToken();
    setIsLoggedIn(false);
    router.push("/login");
  };

  if (checking) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
