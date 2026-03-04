"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ResponseViewer, CopyButton } from "./ResponseViewer";
import type { ProviderResult } from "@/lib/types";

interface ConsensusAnswerProps {
  results: Map<string, ProviderResult>;
  activeProviders: Set<string>;
}

export function ConsensusAnswer({ results, activeProviders }: ConsensusAnswerProps) {
  const { primaryResult, successCount, totalCount } = useMemo(() => {
    let primary: ProviderResult | null = null;
    let successes = 0;
    const total = results.size + activeProviders.size;

    for (const [name, r] of results) {
      if (r.success && typeof r.response === "string" && name !== "Google Search") {
        successes++;
        if (!primary) primary = r;
      } else if (r.success) {
        successes++;
      }
    }

    return { primaryResult: primary, successCount: successes, totalCount: total };
  }, [results, activeProviders]);

  if (!primaryResult || activeProviders.size > 0) return null;

  const responseText = typeof primaryResult.response === "string" ? primaryResult.response : "";

  return (
    <Card className="border-primary/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Answer</span>
            <Badge variant="outline" className="text-xs font-normal">
              {primaryResult.provider} &middot; {primaryResult.model}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            {primaryResult.response_time != null && (
              <span className="text-xs text-muted-foreground">{primaryResult.response_time}s</span>
            )}
            <CopyButton text={responseText} />
            <Badge variant="secondary" className="text-xs">
              {successCount}/{totalCount} providers
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="max-h-[500px] overflow-y-auto">
          <ResponseViewer content={responseText} />
        </div>
      </CardContent>
    </Card>
  );
}
