"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [config, setConfig] = useState<Config | null>(null);
  const [health, setHealth] = useState<Map<string, ProviderHealth>>(new Map());
  const [checkingHealth, setCheckingHealth] = useState(false);

  useEffect(() => {
    api.get<{ providers: ProviderInfo[] }>("/api/providers").then((d) => setProviders(d.providers));
    api.get<Config>("/api/config").then(setConfig);
  }, []);

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

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Settings</h2>
      <p className="text-sm text-muted-foreground">
        Configuration is managed through the .env file on the server. This page shows the
        current read-only configuration.
      </p>

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
              return (
                <div
                  key={p.id}
                  className="flex items-center justify-between rounded-md border p-3"
                >
                  <div>
                    <span className="font-medium">{p.name}</span>
                    {p.model && (
                      <span className="ml-2 text-sm text-muted-foreground">{p.model}</span>
                    )}
                    <div className="mt-1 flex gap-2">
                      {p.web_search_supported && (
                        <Badge variant={p.web_search_default ? "default" : "secondary"} className="text-xs">
                          Web Search {p.web_search_default ? "ON" : "OFF"}
                        </Badge>
                      )}
                      {p.deep_research_supported && (
                        <Badge variant={p.deep_research_default ? "default" : "secondary"} className="text-xs">
                          Deep Research {p.deep_research_default ? "ON" : "OFF"}
                        </Badge>
                      )}
                    </div>
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
