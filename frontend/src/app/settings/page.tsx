"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAppModeContext } from "@/components/layout/AppModeProvider";
import type { ProviderInfo, ProviderHealth } from "@/lib/types";

interface Config {
  models: Record<string, string>;
  max_tokens: number;
  temperature: number;
  configured_providers: string[];
  web_search: Record<string, boolean>;
  deep_research: Record<string, boolean>;
}

export default function SettingsPage() {
  const { aiseoMode, toggleAiseoMode } = useAppModeContext();
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [config, setConfig] = useState<Config | null>(null);
  const [health, setHealth] = useState<Map<string, ProviderHealth>>(new Map());
  const [checkingHealth, setCheckingHealth] = useState(false);

  const refreshProviders = useCallback(() => {
    api.get<{ providers: ProviderInfo[] }>("/api/providers").then((d) => setProviders(d.providers));
  }, []);

  useEffect(() => {
    refreshProviders();
    api.get<Config>("/api/config").then(setConfig);
  }, [refreshProviders]);

  const checkHealth = async () => {
    setCheckingHealth(true);
    try {
      const { results } = await api.get<{ results: ProviderHealth[] }>("/api/providers/health");
      const map = new Map<string, ProviderHealth>();
      for (const r of results) map.set(r.provider, r);
      setHealth(map);
    } catch {
      // ignore
    } finally {
      setCheckingHealth(false);
    }
  };

  const toggleDefault = async (
    type: "web_search" | "deep_research",
    providerId: string,
    currentValue: boolean,
  ) => {
    try {
      await api.post("/api/config/defaults", {
        [type]: { [providerId]: !currentValue },
      });
      // Refresh provider data to get updated defaults
      refreshProviders();
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Settings</h2>
      <p className="text-sm text-muted-foreground">
        Toggle web search and deep research defaults per provider. Changes take effect immediately
        but reset on server restart. Edit .env for permanent changes.
      </p>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">AISEO Mode</CardTitle>
          <CardDescription>
            Enable AISEO mode to access marketing research tools including AI-powered response
            analysis, advanced query options, and competitive insights.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium">
                {aiseoMode ? "AISEO Mode is ON" : "AISEO Mode is OFF"}
              </span>
              <p className="text-xs text-muted-foreground mt-1">
                {aiseoMode
                  ? "Analysis page, advanced query options, and AISEO checkboxes are visible."
                  : "Showing clean search interface. Toggle on to access marketing research tools."}
              </p>
            </div>
            <Button
              variant={aiseoMode ? "default" : "outline"}
              size="sm"
              onClick={toggleAiseoMode}
            >
              {aiseoMode ? "Disable" : "Enable"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Configured Providers</span>
              <p className="text-lg font-semibold">
                {providers.filter((p) => p.configured).length} / {providers.length}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">App Mode</span>
              <p className="text-lg font-semibold">{aiseoMode ? "AISEO Research" : "General Search"}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            Providers
            <Button
              variant="outline"
              size="sm"
              onClick={checkHealth}
              disabled={checkingHealth}
            >
              {checkingHealth ? "Checking..." : "Test Connections"}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {providers.map((p) => {
              const h = health.get(p.name);
              const isPerplexityWeb = p.id === "perplexity";
              return (
                <div
                  key={p.id}
                  className="rounded-md border p-3"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-medium">{p.name}</span>
                      {p.model && (
                        <span className="ml-2 text-sm text-muted-foreground">{p.model}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {h && (
                        <div className="text-right">
                          {h.status === "ok" ? (
                            <Badge variant="default" className="bg-green-600 text-xs">
                              OK {h.latency != null && `(${h.latency}s)`}
                            </Badge>
                          ) : h.status === "not_configured" ? (
                            <Badge variant="secondary" className="text-xs">N/A</Badge>
                          ) : (
                            <Badge variant="destructive" className="text-xs" title={h.error}>
                              Error {h.latency != null && `(${h.latency}s)`}
                            </Badge>
                          )}
                        </div>
                      )}
                      <Badge variant={p.configured ? "default" : "outline"}>
                        {p.configured ? "Active" : "Not configured"}
                      </Badge>
                    </div>
                  </div>

                  {/* Feature toggles */}
                  {(p.web_search_supported || p.deep_research_supported) && (
                    <div className="mt-2 flex gap-2">
                      {p.web_search_supported && (
                        <button
                          onClick={() => toggleDefault("web_search", p.id, p.web_search_default)}
                          disabled={isPerplexityWeb}
                          className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                            p.web_search_default
                              ? "border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-300"
                              : "border-input bg-background text-muted-foreground hover:bg-muted"
                          } ${isPerplexityWeb ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
                          title={isPerplexityWeb ? "Perplexity always uses web search" : `Toggle web search default for ${p.name}`}
                        >
                          <span className={`inline-block h-2 w-2 rounded-full ${p.web_search_default ? "bg-blue-500" : "bg-muted-foreground/30"}`} />
                          Web Search {p.web_search_default ? "ON" : "OFF"}
                        </button>
                      )}
                      {p.deep_research_supported && (
                        <button
                          onClick={() => toggleDefault("deep_research", p.id, p.deep_research_default)}
                          className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                            p.deep_research_default
                              ? "border-purple-300 bg-purple-50 text-purple-700 dark:border-purple-800 dark:bg-purple-950 dark:text-purple-300"
                              : "border-input bg-background text-muted-foreground hover:bg-muted"
                          }`}
                          title={`Toggle deep research default for ${p.name}`}
                        >
                          <span className={`inline-block h-2 w-2 rounded-full ${p.deep_research_default ? "bg-purple-500" : "bg-muted-foreground/30"}`} />
                          Deep Research {p.deep_research_default ? "ON" : "OFF"}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {config && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Max Tokens</span>
                <p className="font-mono">{config.max_tokens}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Temperature</span>
                <p className="font-mono">{config.temperature}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
