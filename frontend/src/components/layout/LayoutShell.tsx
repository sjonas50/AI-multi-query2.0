"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Sidebar } from "./Sidebar";

export function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isLoggedIn } = useAuth();

  if (pathname === "/login" || pathname === "/register" || !isLoggedIn) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
