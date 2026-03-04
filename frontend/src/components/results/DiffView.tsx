"use client";

import { useState, useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import type { Claim } from "@/lib/types";

interface DiffViewProps {
  claims: Claim[];
  providers: string[];
}

function ClaimCard({ claim, provider }: { claim: Claim; provider: string }) {
  return (
    <div className="rounded-md border p-2.5 text-sm">
      <div className="flex items-start gap-2">
        <Badge variant="outline" className="shrink-0 text-[10px]">{claim.category}</Badge>
        <span className="font-medium">{claim.claim}</span>
      </div>
      {claim.details[provider] && (
        <p className="mt-1 text-xs text-muted-foreground">{claim.details[provider]}</p>
      )}
    </div>
  );
}

function DisagreementCard({ claim, providerA, providerB }: { claim: Claim; providerA: string; providerB: string }) {
  return (
    <div className="rounded-md border border-red-200 dark:border-red-900 p-2.5 text-sm">
      <div className="flex items-start gap-2">
        <Badge variant="outline" className="shrink-0 text-[10px]">{claim.category}</Badge>
        <span className="font-medium">{claim.claim}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-3">
        <div className="text-xs">
          <span className="font-medium">{providerA}</span>
          <span className="ml-1 text-muted-foreground">({claim.providers[providerA]})</span>
          <p className="mt-0.5 text-muted-foreground">{claim.details[providerA] || "Not addressed"}</p>
        </div>
        <div className="text-xs">
          <span className="font-medium">{providerB}</span>
          <span className="ml-1 text-muted-foreground">({claim.providers[providerB]})</span>
          <p className="mt-0.5 text-muted-foreground">{claim.details[providerB] || "Not addressed"}</p>
        </div>
      </div>
    </div>
  );
}

export function DiffView({ claims, providers }: DiffViewProps) {
  const [providerA, setProviderA] = useState(providers[0] || "");
  const [providerB, setProviderB] = useState(providers[1] || "");

  const { onlyA, onlyB, both, disagreements } = useMemo(() => {
    const onlyA = claims.filter(
      (c) => c.providers[providerA] !== "not_mentioned" && c.providers[providerB] === "not_mentioned",
    );
    const onlyB = claims.filter(
      (c) => c.providers[providerB] !== "not_mentioned" && c.providers[providerA] === "not_mentioned",
    );
    const both = claims.filter(
      (c) => c.providers[providerA] !== "not_mentioned" && c.providers[providerB] !== "not_mentioned",
    );
    const disagreements = both.filter((c) => c.providers[providerA] !== c.providers[providerB]);
    return { onlyA, onlyB, both, disagreements };
  }, [claims, providerA, providerB]);

  return (
    <div className="space-y-4">
      {/* Provider selectors */}
      <div className="flex items-center gap-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Provider A</label>
          <select
            value={providerA}
            onChange={(e) => setProviderA(e.target.value)}
            className="block mt-1 rounded-md border bg-background px-3 py-1.5 text-sm"
          >
            {providers.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <span className="mt-5 text-muted-foreground font-medium">vs</span>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Provider B</label>
          <select
            value={providerB}
            onChange={(e) => setProviderB(e.target.value)}
            className="block mt-1 rounded-md border bg-background px-3 py-1.5 text-sm"
          >
            {providers.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      {providerA === providerB ? (
        <p className="text-sm text-muted-foreground">Select two different providers to compare.</p>
      ) : (
        <>
          {/* Summary stats */}
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>Shared: {both.length}</span>
            <span>Only {providerA}: {onlyA.length}</span>
            <span>Only {providerB}: {onlyB.length}</span>
            {disagreements.length > 0 && (
              <span className="text-red-600 dark:text-red-400">Disagreements: {disagreements.length}</span>
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* Left column: Only in A */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                Only in {providerA}
                <Badge variant="outline" className="text-xs">{onlyA.length}</Badge>
              </h4>
              {onlyA.length === 0 && (
                <p className="text-xs text-muted-foreground">No unique claims</p>
              )}
              {onlyA.map((c, i) => (
                <ClaimCard key={i} claim={c} provider={providerA} />
              ))}
            </div>

            {/* Right column: Only in B */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                Only in {providerB}
                <Badge variant="outline" className="text-xs">{onlyB.length}</Badge>
              </h4>
              {onlyB.length === 0 && (
                <p className="text-xs text-muted-foreground">No unique claims</p>
              )}
              {onlyB.map((c, i) => (
                <ClaimCard key={i} claim={c} provider={providerB} />
              ))}
            </div>
          </div>

          {/* Disagreements */}
          {disagreements.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                Disagreements
                <Badge variant="destructive" className="text-xs">{disagreements.length}</Badge>
              </h4>
              {disagreements.map((c, i) => (
                <DisagreementCard key={i} claim={c} providerA={providerA} providerB={providerB} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
