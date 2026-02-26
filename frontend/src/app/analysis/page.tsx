"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface TrendWeek {
  week_start: string;
  summary: {
    avg_ugc_percentage: number;
    avg_owned_percentage: number;
    avg_authority_percentage: number;
    total_analyses: number;
    negative_content_count: number;
  };
}

interface AnalysisHistoryItem {
  id: number;
  timestamp: string;
  query: string;
  provider: string;
  companies_mentioned: string[];
  sentiment: string;
  ugc_percentage: number;
}

interface DomainData {
  domain: string;
  count: number;
  type?: string;
}

interface CompetitorData {
  name: string;
  mentions: number;
  sentiment?: string;
}

const COLORS = ["#3b82f6", "#22c55e", "#ef4444", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

export default function AnalysisPage() {
  const [trends, setTrends] = useState<TrendWeek[]>([]);
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [domains, setDomains] = useState<DomainData[]>([]);
  const [competitors, setCompetitors] = useState<CompetitorData[]>([]);
  const [providerFilter, setProviderFilter] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"trends" | "domains" | "competitors">("trends");

  useEffect(() => {
    api.get<TrendWeek[]>("/api/analysis/trends?weeks=12").then(setTrends).catch(() => {});
    api
      .get<{ items: AnalysisHistoryItem[] }>("/api/analysis/history?limit=50")
      .then((d) => setHistory(d.items))
      .catch(() => {});
    api.get<DomainData[]>("/api/analysis/domains").then(setDomains).catch(() => {});
    api.get<CompetitorData[]>("/api/analysis/competitors").then(setCompetitors).catch(() => {});
  }, []);

  const chartData = [...trends].reverse().map((t) => ({
    week: t.week_start,
    UGC: t.summary.avg_ugc_percentage,
    Owned: t.summary.avg_owned_percentage,
    Authority: t.summary.avg_authority_percentage,
    Analyses: t.summary.total_analyses,
    Negative: t.summary.negative_content_count,
  }));

  const filteredHistory = providerFilter
    ? history.filter((h) => h.provider === providerFilter)
    : history;

  const uniqueProviders = [...new Set(history.map((h) => h.provider))];

  const sentimentCounts = filteredHistory.reduce(
    (acc, h) => {
      acc[h.sentiment] = (acc[h.sentiment] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );
  const sentimentData = Object.entries(sentimentCounts).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Analysis Dashboard</h2>

      {/* Tab navigation */}
      <div className="flex gap-2 border-b pb-2">
        {(["trends", "domains", "competitors"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`rounded-t px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Trends Tab */}
      {activeTab === "trends" && (
        <>
          {chartData.length > 0 ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Domain Distribution Trends</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="UGC" stroke="#ef4444" strokeWidth={2} />
                      <Line type="monotone" dataKey="Owned" stroke="#3b82f6" strokeWidth={2} />
                      <Line type="monotone" dataKey="Authority" stroke="#22c55e" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Analysis Volume & Negative Signals</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="Analyses" fill="#3b82f6" />
                      <Bar dataKey="Negative" fill="#ef4444" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No trend data available. Enable enhanced analysis and run queries with
                tracking to see trends here.
              </CardContent>
            </Card>
          )}

          {/* Sentiment overview */}
          {sentimentData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sentiment Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-8">
                  <div className="w-48 h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={sentimentData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={70}
                          label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                        >
                          {sentimentData.map((_, i) => (
                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex flex-col gap-1">
                    {sentimentData.map((s, i) => (
                      <div key={s.name} className="flex items-center gap-2 text-sm">
                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                        <span className="capitalize">{s.name}</span>
                        <span className="text-muted-foreground">({s.value})</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Domains Tab */}
      {activeTab === "domains" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Cited Domains</CardTitle>
          </CardHeader>
          <CardContent>
            {domains.length > 0 ? (
              <div className="space-y-2">
                {domains.slice(0, 20).map((d, i) => (
                  <div key={d.domain} className="flex items-center justify-between rounded border p-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground w-6">#{i + 1}</span>
                      <span className="text-sm font-medium">{d.domain}</span>
                      {d.type && (
                        <Badge variant="secondary" className="text-xs">{d.type}</Badge>
                      )}
                    </div>
                    <Badge variant="outline">{d.count} citations</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No domain data available. Run queries with enhanced analysis enabled.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Competitors Tab */}
      {activeTab === "competitors" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Competitor Mentions</CardTitle>
          </CardHeader>
          <CardContent>
            {competitors.length > 0 ? (
              <div className="space-y-2">
                {competitors.map((c) => (
                  <div key={c.name} className="flex items-center justify-between rounded border p-2">
                    <span className="text-sm font-medium">{c.name}</span>
                    <div className="flex items-center gap-2">
                      {c.sentiment && (
                        <Badge
                          variant={
                            c.sentiment === "positive" ? "default" :
                            c.sentiment === "negative" ? "destructive" : "secondary"
                          }
                          className="text-xs"
                        >
                          {c.sentiment}
                        </Badge>
                      )}
                      <Badge variant="outline">{c.mentions} mentions</Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No competitor data available. Run queries with enhanced analysis enabled.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Analyses table */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Recent Analyses</h3>
          {uniqueProviders.length > 1 && (
            <div className="flex gap-1">
              <button
                onClick={() => setProviderFilter("")}
                className={`rounded px-2 py-1 text-xs ${
                  !providerFilter ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                }`}
              >
                All
              </button>
              {uniqueProviders.map((p) => (
                <button
                  key={p}
                  onClick={() => setProviderFilter(p)}
                  className={`rounded px-2 py-1 text-xs ${
                    providerFilter === p ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-2 text-left font-medium">Query</th>
                <th className="px-4 py-2 text-left font-medium">Provider</th>
                <th className="px-4 py-2 text-left font-medium">Sentiment</th>
                <th className="px-4 py-2 text-left font-medium">Companies</th>
                <th className="px-4 py-2 text-left font-medium">UGC %</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((item) => (
                <tr key={item.id} className="border-b">
                  <td className="px-4 py-2 max-w-[300px] truncate">{item.query}</td>
                  <td className="px-4 py-2">{item.provider}</td>
                  <td className="px-4 py-2">
                    <Badge
                      variant={
                        item.sentiment === "positive"
                          ? "default"
                          : item.sentiment === "negative"
                            ? "destructive"
                            : "secondary"
                      }
                      className="text-xs"
                    >
                      {item.sentiment}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-xs text-muted-foreground">
                    {item.companies_mentioned.slice(0, 3).join(", ")}
                  </td>
                  <td className="px-4 py-2 text-xs font-mono">
                    {item.ugc_percentage > 0 ? `${item.ugc_percentage}%` : "-"}
                  </td>
                </tr>
              ))}
              {filteredHistory.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    No analysis data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
