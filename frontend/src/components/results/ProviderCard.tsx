"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ResponseViewer, CopyButton, StreamingCursor } from "./ResponseViewer";
import { GoogleSearchResults } from "./GoogleSearchResults";
import { AnalysisSummary } from "./AnalysisSummary";
import { SourcesPanel } from "./SourcesPanel";
import { extractCitations } from "@/lib/citations";
import type { ProviderResult, SearchResult } from "@/lib/types";

interface ProviderCardProps {
  provider: string;
  result?: ProviderResult;
  isLoading?: boolean;
  retryAttempt?: number;
}

export function ProviderCard({
  provider,
  result,
  isLoading,
  retryAttempt,
}: ProviderCardProps) {
  const [thinkingExpanded, setThinkingExpanded] = useState(false);

  const isStreaming = result?.streaming || result?.streamingThinking;
  const hasTokens = !!(
    result &&
    (typeof result.response === "string" && result.response.length > 0) ||
    result?.thinking
  );

  const statusMessage = result?.statusMessage;

  // Show skeleton only when loading and no tokens have arrived yet
  if (isLoading && !hasTokens) {
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
                  {statusMessage || "Querying..."}
                </Badge>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {statusMessage ? (
            <p className="text-sm text-muted-foreground animate-pulse">{statusMessage}</p>
          ) : (
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  if (!result) return null;

  const isSearch = provider === "Google Search";
  const hasError = !!result.error;
  const responseText = typeof result.response === "string" ? result.response : "";
  const citations = !isSearch && responseText && !isStreaming ? extractCitations(responseText) : null;

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
            {isStreaming && (
              <Badge variant="secondary" className="animate-pulse text-xs">
                Streaming...
              </Badge>
            )}
            {result.response_time != null && (
              <span className="text-xs text-muted-foreground">{result.response_time}s</span>
            )}
            {!isStreaming && (
              <Badge variant={hasError ? "destructive" : "default"} className="text-xs">
                {hasError ? "Error" : "Success"}
              </Badge>
            )}
          </div>
        </CardTitle>
        {!isStreaming && !hasError && result.response_length != null && (
          <p className="text-xs text-muted-foreground">
            {result.response_length.toLocaleString()} chars
          </p>
        )}
      </CardHeader>

      <CardContent>
        {hasError ? (
          <p className="text-sm text-red-600 dark:text-red-400">{result.error}</p>
        ) : (
          <>
            {/* Thinking section */}
            {result.thinking && (
              <div className="mb-3">
                <button
                  type="button"
                  onClick={() => setThinkingExpanded(!thinkingExpanded)}
                  className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  <svg
                    className={`h-3 w-3 transition-transform ${thinkingExpanded ? "rotate-90" : ""}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Thinking
                  {result.streamingThinking && <StreamingCursor />}
                  {!result.streamingThinking && (
                    <span className="text-muted-foreground/60">
                      ({result.thinking.length.toLocaleString()} chars)
                    </span>
                  )}
                </button>
                {thinkingExpanded && (
                  <div className="mt-2 max-h-[300px] overflow-y-auto rounded-md bg-muted/50 p-3 text-xs text-muted-foreground italic whitespace-pre-wrap">
                    {result.thinking}
                    {result.streamingThinking && <StreamingCursor />}
                  </div>
                )}
              </div>
            )}

            {/* Response */}
            {isSearch && Array.isArray(result.response) ? (
              <GoogleSearchResults items={result.response as SearchResult[]} />
            ) : (
              <div>
                {responseText && !isStreaming && (
                  <div className="mb-2 flex justify-end">
                    <CopyButton text={responseText} />
                  </div>
                )}
                <div className="max-h-[600px] overflow-y-auto">
                  <ResponseViewer content={responseText} streaming={result.streaming} />
                </div>
              </div>
            )}

            {citations && citations.sources.length > 0 && (
              <SourcesPanel sources={citations.sources} />
            )}

            {result.analysis && <AnalysisSummary data={result.analysis} />}
          </>
        )}
      </CardContent>
    </Card>
  );
}
