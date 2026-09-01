"use client";

import { useCallback, useRef, useState } from "react";

import { apiBaseUrl, ProRequiredError } from "@/lib/api";

type WorkoutStreamState = {
  content: string;
  isStreaming: boolean;
  error: string | null;
};

type WorkoutStreamReturn = WorkoutStreamState & {
  generate: (payload: {
    goal: string;
    experience_level?: string;
    split?: string;
    equipment?: string;
  }) => Promise<void>;
  abort: () => void;
  reset: () => void;
};

/**
 * Custom hook for SSE streaming AI workout generation.
 * Mirrors the meal plan streaming pattern exactly.
 */
export function useWorkoutStream(): WorkoutStreamReturn {
  const [state, setState] = useState<WorkoutStreamState>({
    content: "",
    isStreaming: false,
    error: null,
  });

  const abortRef = useRef<AbortController | null>(null);

  const generate = useCallback(
    async (payload: {
      goal: string;
      experience_level?: string;
      split?: string;
      equipment?: string;
    }) => {
      // Abort any previous stream
      abortRef.current?.abort();

      const controller = new AbortController();
      abortRef.current = controller;

      setState({ content: "", isStreaming: true, error: null });

      try {
        const response = await fetch(`${apiBaseUrl}/api/ai/workout/generate`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        // Paywall interceptor
        if (response.status === 403) {
          let detail: Record<string, unknown> | null = null;
          try {
            detail = await response.json();
          } catch {
            // ignore
          }
          if (
            detail &&
            typeof detail.detail === "object" &&
            detail.detail !== null &&
            (detail.detail as Record<string, unknown>).code === "PRO_REQUIRED"
          ) {
            window.dispatchEvent(new Event("pro-required"));
            throw new ProRequiredError(
              "This feature requires an active Pro subscription.",
            );
          }
          throw new Error("Access denied. Upgrade to Pro to use this feature.");
        }

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE lines
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6).trim();

            if (data === "[DONE]") {
              setState((prev) => ({ ...prev, isStreaming: false }));
              return;
            }

            try {
              const parsed = JSON.parse(data) as { text?: string; error?: string };
              if (parsed.error) {
                setState((prev) => ({
                  ...prev,
                  isStreaming: false,
                  error: parsed.error!,
                }));
                return;
              }
              if (parsed.text) {
                setState((prev) => ({
                  ...prev,
                  content: prev.content + parsed.text,
                }));
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }

        setState((prev) => ({ ...prev, isStreaming: false }));
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          // User aborted — don't show error
          setState((prev) => ({ ...prev, isStreaming: false }));
          return;
        }
        if (err instanceof ProRequiredError) {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            error: null, // Don't show error — upgrade modal is shown
          }));
          return;
        }
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: err instanceof Error ? err.message : "Streaming failed",
        }));
      }
    },
    [],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState({ content: "", isStreaming: false, error: null });
  }, []);

  return { ...state, generate, abort, reset };
}
