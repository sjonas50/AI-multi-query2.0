import { fetchEventSource } from "@microsoft/fetch-event-source";
import type { SSEEvent } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAYS = [1000, 3000, 5000];

export function streamQuery(
  queryId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (err: unknown) => void,
  onReconnecting?: (attempt: number) => void,
): AbortController {
  const controller = new AbortController();
  const token = localStorage.getItem("auth_token");
  let reconnectAttempts = 0;
  let completed = false;

  const connect = () => {
    fetchEventSource(`${API_BASE}/api/queries/${queryId}/stream`, {
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${token}`,
      },
      onmessage(msg) {
        reconnectAttempts = 0; // reset on successful message
        try {
          const data = JSON.parse(msg.data);
          const event: SSEEvent = { event: msg.event, data };
          onEvent(event);
          if (msg.event === "all_complete" || msg.event === "cancelled" || msg.event === "timeout") {
            completed = true;
          }
        } catch {
          // ignore malformed events
        }
      },
      onerror(err) {
        if (completed || controller.signal.aborted) {
          throw err; // stop retrying
        }

        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_DELAYS[reconnectAttempts] ?? 5000;
          reconnectAttempts++;
          onReconnecting?.(reconnectAttempts);
          // Return delay to let fetchEventSource retry after that duration
          return delay;
        }

        onError?.(err);
        throw err; // stop retrying after max attempts
      },
      openWhenHidden: true,
    });
  };

  connect();
  return controller;
}
