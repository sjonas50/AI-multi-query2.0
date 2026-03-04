import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/layout/AuthProvider";
import { Sidebar } from "@/components/layout/Sidebar";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { AppModeProvider } from "@/components/layout/AppModeProvider";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Search",
  description: "Multi-LLM search and comparison tool",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ThemeProvider>
          <AuthProvider>
            <AppModeProvider>
              <LayoutShell>{children}</LayoutShell>
            </AppModeProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
