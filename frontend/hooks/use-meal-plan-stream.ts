"use client";

import { useCallback, useRef, useState } from "react";

import { apiBaseUrl } from "@/lib/api";

export type MealPlanStreamRequest = {
  target_calories?: number | null;
  protein_g?: number | null;
  dietary_preferences?: string[];
  allergies?: string[];
  cuisine_type?: string | null;
};

type MealPlanStreamState = {
  content: string;
  isStreaming: boolean;
  error: string | null;
  isSandbox: boolean;
};

/**
 * Custom hook for streaming AI-generated meal plans via SSE.
 *
 * Usage:
 * ```ts
 * const { content, isStreaming, error, isSandbox, generate } = useMealPlanStream();
 * await generate({ target_calories: 2000, cuisine_type: "South Asian" });
 * ```
 */
export function useMealPlanStream() {
  const [state, setState] = useState<MealPlanStreamState>({
    content: "",
    isStreaming: false,
    error: null,
    isSandbox: false,
  });
  const abortRef = useRef<AbortController | null>(null);

  const generate = useCallback(async (payload: MealPlanStreamRequest) => {
    // Abort any in-flight stream
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ content: "", isStreaming: true, error: null, isSandbox: false });

    try {
      const response = await fetch(`${apiBaseUrl}/api/ai/meal-plans/generate`, {
        method: "POST",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        signal: controller.signal,
      });

      // ── Paywall interceptor ──────────────────────────────────────────
      if (response.status === 403) {
        let detail: Record<string, unknown> | null = null;
        try {
          const errBody = await response.json();
          detail = errBody.detail ?? null;
        } catch {
          // ignore parse failure
        }

        if (detail?.code === "PRO_REQUIRED") {
          window.dispatchEvent(new Event("pro-required"));
          setState({
            content: "",
            isStreaming: false,
            error: "This feature requires a Pro subscription.",
            isSandbox: false,
          });
          return;
        }

        setState({
          content: "",
          isStreaming: false,
          error: `Access denied (${response.status}).`,
          isSandbox: false,
        });
        return;
      }

      if (!response.ok) {
        setState({
          content: "",
          isStreaming: false,
          error: `Request failed with status ${response.status}`,
          isSandbox: false,
        });
        return;
      }

      // ── Read SSE stream ──────────────────────────────────────────────
      const reader = response.body?.getReader();
      if (!reader) {
        setState({
          content: "",
          isStreaming: false,
          error: "Response body is not readable.",
          isSandbox: false,
        });
        return;
      }

      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Split by double-newline (SSE record boundary)
        const records = buffer.split("\n\n");
        // Keep the last incomplete record in the buffer
        buffer = records.pop() ?? "";

        for (const record of records) {
          const lines = record.split("\n");
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;

            const data = line.slice(6); // strip "data: "

            if (data === "[DONE]") {
              setState((prev) => ({ ...prev, isStreaming: false }));
              return;
            }

            try {
              const parsed = JSON.parse(data) as {
                text?: string;
                error?: string;
                sandbox?: boolean;
              };
              if (parsed.error) {
                setState((prev) => ({
                  ...prev,
                  isStreaming: false,
                  error: parsed.error!,
                }));
                return;
              }
              if (parsed.sandbox) {
                setState((prev) => ({ ...prev, isSandbox: true }));
              }
              if (parsed.text) {
                setState((prev) => ({
                  ...prev,
                  content: prev.content + parsed.text,
                }));
              }
            } catch {
              // Skip unparseable lines
            }
          }
        }
      }

      // Stream ended without [DONE]
      setState((prev) => ({ ...prev, isStreaming: false }));
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // User aborted — no state update needed
        return;
      }
      setState({
        content: "",
        isStreaming: false,
        error: err instanceof Error ? err.message : "Stream failed.",
        isSandbox: false,
      });
    }
  }, []);

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState({ content: "", isStreaming: false, error: null, isSandbox: false });
  }, []);

  return { ...state, generate, abort, reset };
}
