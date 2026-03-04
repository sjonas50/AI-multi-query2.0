"use client";

import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { streamQuery } from "@/lib/sse";
import type { ProviderResult } from "@/lib/types";

type QueryStatus = "idle" | "running" | "complete" | "error" | "cancelled";

export function useQueryExecution() {
  const [results, setResults] = useState<Map<string, ProviderResult>>(new Map());
  const [activeProviders, setActiveProviders] = useState<Set<string>>(new Set());
  const [retryingProviders, setRetryingProviders] = useState<Map<string, number>>(new Map());
  const [status, setStatus] = useState<QueryStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [savedFilename, setSavedFilename] = useState<string | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  const controllerRef = useRef<AbortController | null>(null);
  const queryIdRef = useRef<string | null>(null);

  const cancel = useCallback(async () => {
    if (queryIdRef.current) {
      try {
        await api.delete(`/api/queries/${queryIdRef.current}`);
      } catch {
        // best effort
      }
    }
    controllerRef.current?.abort();
    setStatus("cancelled");
    setActiveProviders(new Set());
    setRetryingProviders(new Map());
    setReconnecting(false);
  }, []);

  const execute = useCallback(
    async (
      query: string,
      providers?: string[],
      options?: {
        analyze?: boolean;
        request_sources?: boolean;
        web_search?: boolean | null;
        deep_research?: boolean | null;
        conversation_id?: string | null;
      },
    ) => {
      setStatus("running");
      setResults(new Map());
      setActiveProviders(new Set());
      setRetryingProviders(new Map());
      setError(null);
      setSavedFilename(null);
      setReconnecting(false);
      setSuggestions([]);
      setSuggestionsLoading(false);

      try {
        const { query_id, conversation_id: conv_id } = await api.post<{
          query_id: string;
          providers: string[];
          conversation_id: string;
        }>(
          "/api/queries",
          {
            query,
            providers: providers?.length ? providers : null,
            analyze: options?.analyze ?? false,
            request_sources: options?.request_sources ?? false,
            web_search: options?.web_search ?? null,
            deep_research: options?.deep_research ?? null,
            conversation_id: options?.conversation_id ?? null,
          },
        );

        setConversationId(conv_id);

        queryIdRef.current = query_id;

        const controller = streamQuery(
          query_id,
          (event) => {
            setReconnecting(false);
            switch (event.event) {
              case "provider_start":
                if (event.data.provider) {
                  setActiveProviders((prev) => new Set([...prev, event.data.provider!]));
                  setRetryingProviders((prev) => {
                    const next = new Map(prev);
                    next.delete(event.data.provider!);
                    return next;
                  });
                }
                break;
              case "provider_retry":
                if (event.data.provider) {
                  setRetryingProviders((prev) => {
                    const next = new Map(prev);
                    next.set(event.data.provider!, event.data.attempt ?? 1);
                    return next;
                  });
                }
                break;
              case "provider_status":
                if (event.data.provider && event.data.message) {
                  setResults((prev) => {
                    const next = new Map(prev);
                    const existing = next.get(event.data.provider!);
                    next.set(event.data.provider!, {
                      ...existing,
                      provider: event.data.provider!,
                      statusMessage: event.data.message!,
                      success: existing?.success ?? true,
                    });
                    return next;
                  });
                }
                break;
              case "provider_thinking":
                if (event.data.provider && event.data.text) {
                  setResults((prev) => {
                    const next = new Map(prev);
                    const existing = next.get(event.data.provider!);
                    next.set(event.data.provider!, {
                      ...existing,
                      provider: event.data.provider!,
                      thinking: (existing?.thinking || "") + event.data.text!,
                      streamingThinking: true,
                      streaming: existing?.streaming ?? false,
                      success: true,
                    });
                    return next;
                  });
                }
                break;
              case "provider_token":
                if (event.data.provider && event.data.text) {
                  setResults((prev) => {
                    const next = new Map(prev);
                    const existing = next.get(event.data.provider!);
                    const currentResponse = typeof existing?.response === "string" ? existing.response : "";
                    next.set(event.data.provider!, {
                      ...existing,
                      provider: event.data.provider!,
                      response: currentResponse + event.data.text!,
                      streaming: true,
                      streamingThinking: false,
                      success: true,
                    });
                    return next;
                  });
                }
                break;
              case "provider_complete":
                if (event.data.provider && event.data.result) {
                  setResults((prev) => {
                    const next = new Map(prev);
                    const existing = next.get(event.data.provider!);
                    // Merge: keep streamed data, overlay with final metadata
                    next.set(event.data.provider!, {
                      ...existing,
                      ...event.data.result!,
                      streaming: false,
                      streamingThinking: false,
                    });
                    return next;
                  });
                  setActiveProviders((prev) => {
                    const next = new Set(prev);
                    next.delete(event.data.provider!);
                    return next;
                  });
                  setRetryingProviders((prev) => {
                    const next = new Map(prev);
                    next.delete(event.data.provider!);
                    return next;
                  });
                }
                break;
              case "provider_error":
                if (event.data.provider) {
                  setResults((prev) => {
                    const next = new Map(prev);
                    next.set(event.data.provider!, {
                      provider: event.data.provider!,
                      error: event.data.error,
                      success: false,
                    });
                    return next;
                  });
                  setActiveProviders((prev) => {
                    const next = new Set(prev);
                    next.delete(event.data.provider!);
                    return next;
                  });
                  setRetryingProviders((prev) => {
                    const next = new Map(prev);
                    next.delete(event.data.provider!);
                    return next;
                  });
                }
                break;
              case "analysis_complete":
                if (event.data.provider && event.data.analysis) {
                  setResults((prev) => {
                    const next = new Map(prev);
                    const existing = next.get(event.data.provider!);
                    if (existing) {
                      next.set(event.data.provider!, {
                        ...existing,
                        analysis: event.data.analysis as ProviderResult["analysis"],
                      });
                    }
                    return next;
                  });
                }
                break;
              case "cancelled":
                setStatus("cancelled");
                setActiveProviders(new Set());
                break;
              case "timeout":
                setStatus("error");
                setError("Query timed out");
                break;
              case "all_complete":
                setStatus("complete");
                setSavedFilename(event.data.filename ?? null);
                if (event.data.conversation_id) {
                  setConversationId(event.data.conversation_id);
                }
                // Fetch suggested follow-up questions
                if (query_id) {
                  setSuggestionsLoading(true);
                  api
                    .get<{ questions: string[] }>(`/api/queries/${query_id}/suggestions`)
                    .then((res) => setSuggestions(res.questions || []))
                    .catch(() => {})
                    .finally(() => setSuggestionsLoading(false));
                }
                break;
            }
          },
          () => {
            setStatus("error");
            setError("Connection lost after retries");
            setReconnecting(false);
          },
          (attempt) => {
            setReconnecting(true);
          },
        );

        controllerRef.current = controller;
      } catch (e) {
        setStatus("error");
        setError(e instanceof Error ? e.message : "Unknown error");
      }
    },
    [],
  );

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    setResults(new Map());
    setActiveProviders(new Set());
    setRetryingProviders(new Map());
    setStatus("idle");
    setError(null);
    setSavedFilename(null);
    setReconnecting(false);
    setConversationId(null);
    setSuggestions([]);
    setSuggestionsLoading(false);
    queryIdRef.current = null;
  }, []);

  return {
    execute,
    cancel,
    reset,
    results,
    activeProviders,
    retryingProviders,
    status,
    error,
    savedFilename,
    reconnecting,
    conversationId,
    suggestions,
    suggestionsLoading,
  };
}
