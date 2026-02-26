"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ResponseViewer, CopyButton } from "./ResponseViewer";
import { GoogleSearchResults } from "./GoogleSearchResults";
import { AnalysisSummary } from "./AnalysisSummary";
import type { ProviderResult, SearchResult } from "@/lib/types";

interface ProviderCardProps {
  provider: string;
  result?: ProviderResult;
  isLoading?: boolean;
  retryAttempt?: number;
}

export function ProviderCard({ provider, result, isLoading, retryAttempt }: ProviderCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between text-base">
            {provider}
            <div className="flex items-center gap-2">
              {retryAttempt && retryAttempt > 0 ? (
                <Badge variant="secondary" className="animate-pulse text-xs">
                  Retry #{retryAttempt}...
                </Badge>
              ) : (
                <Badge variant="secondary" className="animate-pulse">
                  Querying...
                </Badge>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result) return null;

  const isSearch = provider === "Google Search";
  const hasError = !!result.error;
  const responseText = typeof result.response === "string" ? result.response : "";

  return (
    <Card className={hasError ? "border-red-300 dark:border-red-800" : ""}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            {provider}
            {result.model && (
              <Badge variant="outline" className="text-xs font-normal">
                {result.model}
              </Badge>
            )}
            {result.web_search && (
              <Badge variant="secondary" className="text-xs font-normal">Web</Badge>
            )}
            {result.deep_research && (
              <Badge variant="secondary" className="text-xs font-normal">Deep</Badge>
            )}
          </span>
          <div className="flex items-center gap-2">
            {result.response_time != null && (
              <span className="text-xs text-muted-foreground">{result.response_time}s</span>
            )}
            {!hasError && !isSearch && responseText && (
              <CopyButton text={responseText} />
            )}
            <Badge variant={hasError ? "destructive" : "default"} className="text-xs">
              {hasError ? "Error" : "Success"}
            </Badge>
          </div>
        </CardTitle>
        {!hasError && result.response_length != null && (
          <p className="text-xs text-muted-foreground">
            {result.response_length.toLocaleString()} chars
          </p>
        )}
      </CardHeader>
      <CardContent>
        {hasError ? (
          <p className="text-sm text-red-600 dark:text-red-400">{result.error}</p>
        ) : isSearch && Array.isArray(result.response) ? (
          <GoogleSearchResults items={result.response as SearchResult[]} />
        ) : (
          <div className="max-h-[600px] overflow-y-auto">
            <ResponseViewer content={responseText} />
          </div>
        )}

        {result.analysis && <AnalysisSummary data={result.analysis} />}
      </CardContent>
    </Card>
  );
}
