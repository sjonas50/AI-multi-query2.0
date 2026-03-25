"use client";

import { useState, useEffect, ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, setToken, clearToken, isAuthenticated } from "@/lib/api";
import { AuthContext } from "@/hooks/useAuth";
import type { User } from "@/lib/types";

const PUBLIC_PATHS = ["/login", "/register"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      setChecking(false);
      return;
    }
    // Validate token and load user info
    api
      .get<User>("/api/auth/me")
      .then((u) => {
        setUser(u);
        setIsLoggedIn(true);
      })
      .catch(() => {
        clearToken();
      })
      .finally(() => setChecking(false));
  }, []);

  useEffect(() => {
    if (!checking && !isLoggedIn && !PUBLIC_PATHS.includes(pathname)) {
      router.push("/login");
    }
  }, [checking, isLoggedIn, pathname, router]);

  const login = async (email: string, password: string) => {
    const res = await api.post<{ token: string; user: User }>("/api/auth/login", {
      email,
      password,
    });
    setToken(res.token);
    setUser(res.user);
    setIsLoggedIn(true);
    router.push("/");
  };

  const logout = () => {
    clearToken();
    setUser(null);
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
    <AuthContext.Provider
      value={{
        isLoggedIn,
        user,
        isAdmin: user?.role === "admin",
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
