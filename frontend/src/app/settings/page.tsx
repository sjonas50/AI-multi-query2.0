"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

interface AiseoConfig {
  config: Record<string, string>;
  competitors: { id: number; name: string; domain: string }[];
  accuracy_facts: { id: number; label: string; field_key: string; correct_value: string }[];
}

export default function SettingsPage() {
  const { aiseoMode, toggleAiseoMode } = useAppModeContext();
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [config, setConfig] = useState<Config | null>(null);
  const [health, setHealth] = useState<Map<string, ProviderHealth>>(new Map());
  const [checkingHealth, setCheckingHealth] = useState(false);

  // AISEO state
  const [aiseoConfig, setAiseoConfig] = useState<AiseoConfig | null>(null);
  const [aiseoSaving, setAiseoSaving] = useState(false);
  const [aiseoStatus, setAiseoStatus] = useState<string | null>(null);

  // Company fields
  const [targetCompany, setTargetCompany] = useState("");
  const [companyDomains, setCompanyDomains] = useState("");
  const [industry, setIndustry] = useState("");

  // Feature toggles
  const [features, setFeatures] = useState({
    analyze_responses: false,
    enable_enhanced_analysis: false,
    track_history: false,
    domain_classification: false,
    negative_signal_detection: false,
    accuracy_verification: false,
    weekly_reporting: false,
  });

  // Model & parameter editing
  const [editModels, setEditModels] = useState<Record<string, string>>({});
  const [editMaxTokens, setEditMaxTokens] = useState("");
  const [editTemperature, setEditTemperature] = useState("");
  const [modelSaving, setModelSaving] = useState(false);
  const [modelStatus, setModelStatus] = useState<string | null>(null);

  // Competitor form
  const [newCompName, setNewCompName] = useState("");
  const [newCompDomain, setNewCompDomain] = useState("");

  // Accuracy fact form
  const [newFactLabel, setNewFactLabel] = useState("");
  const [newFactKey, setNewFactKey] = useState("");
  const [newFactValue, setNewFactValue] = useState("");

  const refreshProviders = useCallback(() => {
    api.get<{ providers: ProviderInfo[] }>("/api/providers").then((d) => setProviders(d.providers));
  }, []);

  const loadAiseoConfig = useCallback(() => {
    api.get<AiseoConfig>("/api/aiseo/config").then((data) => {
      setAiseoConfig(data);
      const c = data.config;
      setTargetCompany(c.target_company || "");
      setCompanyDomains(c.company_domains || "");
      setIndustry(c.industry || "");
      setFeatures({
        analyze_responses: c.analyze_responses === "true",
        enable_enhanced_analysis: c.enable_enhanced_analysis === "true",
        track_history: c.track_history === "true",
        domain_classification: c.domain_classification === "true",
        negative_signal_detection: c.negative_signal_detection === "true",
        accuracy_verification: c.accuracy_verification === "true",
        weekly_reporting: c.weekly_reporting === "true",
      });
    }).catch(() => {});
  }, []);

  useEffect(() => {
    refreshProviders();
    api.get<Config>("/api/config").then((c) => {
      setConfig(c);
      setEditModels(c.models);
      setEditMaxTokens(String(c.max_tokens));
      setEditTemperature(String(c.temperature));
    });
    loadAiseoConfig();
  }, [refreshProviders, loadAiseoConfig]);

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
      refreshProviders();
    } catch {
      // ignore
    }
  };

  // --- Model & parameter handlers ---

  const saveModelConfig = async () => {
    setModelSaving(true);
    setModelStatus(null);
    try {
      const payload: Record<string, unknown> = {
        models: editModels,
        max_tokens: parseInt(editMaxTokens) || 8000,
        temperature: parseFloat(editTemperature) || 0.7,
      };
      const res = await api.post<Config>("/api/config/defaults", payload);
      setConfig((prev) => prev ? { ...prev, ...res } : prev);
      setModelStatus("Saved");
      setTimeout(() => setModelStatus(null), 2000);
    } catch {
      setModelStatus("Error saving");
    } finally {
      setModelSaving(false);
    }
  };

  // --- AISEO handlers ---

  const saveCompanyConfig = async () => {
    setAiseoSaving(true);
    setAiseoStatus(null);
    try {
      const updates: Record<string, string> = {
        target_company: targetCompany,
        company_domains: companyDomains,
        industry: industry,
        ...Object.fromEntries(
          Object.entries(features).map(([k, v]) => [k, v ? "true" : "false"])
        ),
      };
      await api.put("/api/aiseo/config", updates);
      setAiseoStatus("Saved");
      setTimeout(() => setAiseoStatus(null), 2000);
    } catch (e) {
      setAiseoStatus("Error saving");
    } finally {
      setAiseoSaving(false);
    }
  };

  const addCompetitor = async () => {
    if (!newCompName.trim() || !newCompDomain.trim()) return;
    try {
      await api.post("/api/aiseo/competitors", { name: newCompName, domain: newCompDomain });
      setNewCompName("");
      setNewCompDomain("");
      loadAiseoConfig();
    } catch {
      // ignore
    }
  };

  const removeCompetitor = async (id: number) => {
    try {
      await api.delete(`/api/aiseo/competitors/${id}`);
      loadAiseoConfig();
    } catch {
      // ignore
    }
  };

  const addFact = async () => {
    if (!newFactLabel.trim() || !newFactKey.trim() || !newFactValue.trim()) return;
    try {
      await api.post("/api/aiseo/accuracy-facts", {
        label: newFactLabel,
        field_key: newFactKey,
        correct_value: newFactValue,
      });
      setNewFactLabel("");
      setNewFactKey("");
      setNewFactValue("");
      loadAiseoConfig();
    } catch {
      // ignore
    }
  };

  const removeFact = async (id: number) => {
    try {
      await api.delete(`/api/aiseo/accuracy-facts/${id}`);
      loadAiseoConfig();
    } catch {
      // ignore
    }
  };

  const toggleFeature = (key: keyof typeof features) => {
    setFeatures((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Settings</h2>
      <p className="text-sm text-muted-foreground">
        Configure providers, AISEO company tracking, and analysis features.
      </p>

      {/* AISEO Mode Toggle */}
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

      {/* Company Setup — only visible when AISEO mode is on */}
      {aiseoMode && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Company Profile</CardTitle>
              <CardDescription>
                Configure the company you&apos;re tracking across AI search results. This drives
                analysis, competitor detection, and accuracy verification.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="target-company">Company Name</Label>
                  <Input
                    id="target-company"
                    placeholder="e.g. Acme Corp"
                    value={targetCompany}
                    onChange={(e) => setTargetCompany(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="industry">Industry</Label>
                  <Input
                    id="industry"
                    placeholder="e.g. Financial Services, SaaS, Healthcare"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="company-domains">Owned Domains</Label>
                <Input
                  id="company-domains"
                  placeholder="e.g. acme.com, careers.acme.com"
                  value={companyDomains}
                  onChange={(e) => setCompanyDomains(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Comma-separated list of domains owned by the company. Used to classify sources as &quot;owned&quot; in analysis.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button onClick={saveCompanyConfig} disabled={aiseoSaving} size="sm">
                  {aiseoSaving ? "Saving..." : "Save Company Profile"}
                </Button>
                {aiseoStatus && (
                  <span className={`text-xs ${aiseoStatus === "Saved" ? "text-green-600 dark:text-green-400" : "text-red-500 dark:text-red-400"}`}>
                    {aiseoStatus}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Analysis Features */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Analysis Features</CardTitle>
              <CardDescription>
                Toggle AI-powered analysis modules. Changes are saved with the company profile.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                {([
                  ["analyze_responses", "AI Response Analysis", "Use GPT to extract companies, sources, and insights from LLM responses"],
                  ["enable_enhanced_analysis", "Enhanced Analysis", "Enable domain classification, negative detection, and historical tracking"],
                  ["domain_classification", "Domain Classification", "Classify cited sources as owned, competitor, UGC, or authority"],
                  ["negative_signal_detection", "Negative Signal Detection", "Detect negative mentions, controversies, and trust issues"],
                  ["accuracy_verification", "Accuracy Verification", "Check responses against known facts (e.g. minimum investment)"],
                  ["track_history", "Historical Tracking", "Store analysis results for trend tracking over time"],
                  ["weekly_reporting", "Weekly Reports", "Generate weekly AISEO summary reports with recommendations"],
                ] as const).map(([key, label, desc]) => (
                  <button
                    key={key}
                    onClick={() => toggleFeature(key)}
                    className={`flex items-start gap-3 rounded-md border p-3 text-left transition-colors ${
                      features[key]
                        ? "border-blue-300 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/30"
                        : "border-input hover:bg-muted/50"
                    }`}
                  >
                    <span className={`mt-0.5 inline-block h-3 w-3 shrink-0 rounded-sm border ${
                      features[key] ? "border-blue-500 bg-blue-500" : "border-muted-foreground/30"
                    }`} />
                    <div>
                      <span className="text-sm font-medium">{label}</span>
                      <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
                    </div>
                  </button>
                ))}
              </div>
              <div className="mt-4">
                <Button onClick={saveCompanyConfig} disabled={aiseoSaving} size="sm">
                  {aiseoSaving ? "Saving..." : "Save Features"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Competitors */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Competitors</CardTitle>
              <CardDescription>
                Companies to track as competitors in analysis. Their domains will be flagged when
                cited as sources in AI responses.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {aiseoConfig?.competitors && aiseoConfig.competitors.length > 0 && (
                <div className="space-y-2">
                  {aiseoConfig.competitors.map((c) => (
                    <div key={c.id} className="flex items-center justify-between rounded-md border px-3 py-2">
                      <div>
                        <span className="text-sm font-medium">{c.name}</span>
                        <span className="ml-2 text-xs text-muted-foreground">{c.domain}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                        onClick={() => removeCompetitor(c.id)}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  placeholder="Company name"
                  value={newCompName}
                  onChange={(e) => setNewCompName(e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="domain.com"
                  value={newCompDomain}
                  onChange={(e) => setNewCompDomain(e.target.value)}
                  className="flex-1"
                />
                <Button size="sm" onClick={addCompetitor} disabled={!newCompName.trim() || !newCompDomain.trim()}>
                  Add
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Accuracy Facts */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Accuracy Facts</CardTitle>
              <CardDescription>
                Known facts about the company that AI responses should get right. Used to flag
                inaccurate claims in analysis.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {aiseoConfig?.accuracy_facts && aiseoConfig.accuracy_facts.length > 0 && (
                <div className="space-y-2">
                  {aiseoConfig.accuracy_facts.map((f) => (
                    <div key={f.id} className="flex items-center justify-between rounded-md border px-3 py-2">
                      <div>
                        <span className="text-sm font-medium">{f.label}</span>
                        <span className="mx-2 text-xs text-muted-foreground">({f.field_key})</span>
                        <Badge variant="secondary" className="text-xs">{f.correct_value}</Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                        onClick={() => removeFact(f.id)}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  placeholder="Label (e.g. Minimum Investment)"
                  value={newFactLabel}
                  onChange={(e) => setNewFactLabel(e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Key (e.g. minimum_investment)"
                  value={newFactKey}
                  onChange={(e) => setNewFactKey(e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Correct value"
                  value={newFactValue}
                  onChange={(e) => setNewFactValue(e.target.value)}
                  className="flex-[0.8]"
                />
                <Button size="sm" onClick={addFact} disabled={!newFactLabel.trim() || !newFactKey.trim() || !newFactValue.trim()}>
                  Add
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* System Status */}
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
            {aiseoMode && targetCompany && (
              <div>
                <span className="text-muted-foreground">Tracking Company</span>
                <p className="text-lg font-semibold">{targetCompany}</p>
              </div>
            )}
            {aiseoMode && aiseoConfig?.competitors && (
              <div>
                <span className="text-muted-foreground">Competitors Tracked</span>
                <p className="text-lg font-semibold">{aiseoConfig.competitors.length}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Providers */}
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
                            <Badge variant="default" className="bg-green-600 dark:bg-green-700 text-xs text-white">
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
            <CardTitle className="text-base">Models & Parameters</CardTitle>
            <CardDescription>
              Configure which model each provider uses and adjust generation parameters.
              API keys remain in your .env file.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Model selections */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Model per Provider</Label>
              <div className="grid gap-3 sm:grid-cols-2">
                {providers
                  .filter((p) => p.configured && p.id !== "google_search")
                  .map((p) => (
                    <div key={p.id} className="space-y-1">
                      <label htmlFor={`model-${p.id}`} className="text-xs text-muted-foreground">
                        {p.name}
                      </label>
                      <Input
                        id={`model-${p.id}`}
                        value={editModels[p.id] || ""}
                        onChange={(e) =>
                          setEditModels((prev) => ({ ...prev, [p.id]: e.target.value }))
                        }
                        className="h-8 font-mono text-sm"
                      />
                    </div>
                  ))}
              </div>
            </div>

            {/* Parameters */}
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-1">
                <Label htmlFor="max-tokens" className="text-xs text-muted-foreground">
                  Max Tokens
                </Label>
                <Input
                  id="max-tokens"
                  type="number"
                  value={editMaxTokens}
                  onChange={(e) => setEditMaxTokens(e.target.value)}
                  className="h-8 font-mono text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="temperature" className="text-xs text-muted-foreground">
                  Temperature
                </Label>
                <Input
                  id="temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={editTemperature}
                  onChange={(e) => setEditTemperature(e.target.value)}
                  className="h-8 font-mono text-sm"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button onClick={saveModelConfig} disabled={modelSaving} size="sm">
                {modelSaving ? "Saving..." : "Save Models & Parameters"}
              </Button>
              {modelStatus && (
                <span className={`text-xs ${modelStatus === "Saved" ? "text-green-600 dark:text-green-400" : "text-red-500 dark:text-red-400"}`}>
                  {modelStatus}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
