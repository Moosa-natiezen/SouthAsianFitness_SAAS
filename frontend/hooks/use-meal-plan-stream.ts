"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useRealtimeRun } from "@trigger.dev/react-hooks";

import { apiBaseUrl } from "@/lib/api";
import type { generateMealPlanTask } from "@/trigger/generate-meal-plan";

export type MealPlanStreamRequest = {
  target_calories?: number | null;
  protein_g?: number | null;
  dietary_preferences?: string[];
  allergies?: string[];
  cuisine_type?: string | null;
};

/** Terminal run statuses that mean the background task did not succeed. */
const FAILED_RUN_STATUSES = [
  "FAILED",
  "CANCELED",
  "CRASHED",
  "SYSTEM_FAILURE",
  "TIMED_OUT",
  "EXPIRED",
] as const;

type MealPlanStreamState = {
  content: string;
  isStreaming: boolean;
  error: string | null;
  isSandbox: boolean;
  /** True when generation was handed off to a background Trigger.dev task. */
  queued: boolean;
  /** Trigger.dev run id for the queued background task. */
  runHandle: string | null;
  /** Public access token used to subscribe to the run's realtime updates. */
  publicAccessToken: string | null;
};

/**
 * Custom hook for AI-generated meal plans.
 *
 * Generation is attempted in two stages:
 * 1. **Enqueue (preferred)** — POSTs to the same-origin `/api/meal-plans/enqueue`
 *    route, which hands the job to a Trigger.dev background task and returns an
 *    immediate run handle. The hook then subscribes to the run with
 *    `useRealtimeRun` and renders the generated markdown when it completes.
 * 2. **Direct SSE fallback** — if the enqueue route is unavailable (Trigger.dev
 *    not configured, missing session cookie, or a transient failure), streams
 *    from the FastAPI backend exactly as before.
 */
export function useMealPlanStream() {
  const [state, setState] = useState<MealPlanStreamState>({
    content: "",
    isStreaming: false,
    error: null,
    isSandbox: false,
    queued: false,
    runHandle: null,
    publicAccessToken: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  // ── Realtime subscription to the queued background run ───────────────
  // Called unconditionally (hooks rules); it no-ops when nothing is queued
  // or no public access token is available.
  const realtime = useRealtimeRun<typeof generateMealPlanTask>(
    state.queued && state.runHandle ? state.runHandle : undefined,
    {
      accessToken: state.publicAccessToken ?? undefined,
      enabled: state.queued && !!state.runHandle && !!state.publicAccessToken,
    },
  );

  // When the background run reaches a terminal state, materialize the result.
  useEffect(() => {
    if (!state.queued) return;

    const run = realtime.run;
    if (!run) return;

    if (run.status === "COMPLETED") {
      const output = run.output as { markdown?: string } | null | undefined;
      if (output?.markdown) {
        setState({
          content: output.markdown,
          isStreaming: false,
          error: null,
          isSandbox: false,
          queued: false,
          runHandle: null,
          publicAccessToken: null,
        });
      }
      return;
    }

    if (FAILED_RUN_STATUSES.includes(run.status as (typeof FAILED_RUN_STATUSES)[number])) {
      setState({
        content: "",
        isStreaming: false,
        error: `Background generation ${run.status
          .toLowerCase()
          .replace(/_/g, " ")}. Please try again.`,
        isSandbox: false,
        queued: false,
        runHandle: null,
        publicAccessToken: null,
      });
      return;
    }
  }, [state.queued, realtime.run]);

  // Surface subscription-level errors (auth/network) instead of hanging.
  useEffect(() => {
    if (!state.queued || !realtime.error) return;
    setState((prev) =>
      prev.queued
        ? {
            ...prev,
            isStreaming: false,
            error: `Could not subscribe to background task: ${realtime.error!.message}`,
            queued: false,
            runHandle: null,
            publicAccessToken: null,
          }
        : prev,
    );
  }, [realtime.error, state.queued]);

  const generate = useCallback(async (payload: MealPlanStreamRequest) => {
    // Abort any in-flight stream
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({
      content: "",
      isStreaming: true,
      error: null,
      isSandbox: false,
      queued: false,
      runHandle: null,
      publicAccessToken: null,
    });

    // ── Stage 1: try the background enqueue route ─────────────────────
    try {
      const enqueueRes = await fetch("/api/meal-plans/enqueue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const enqueueData = (await enqueueRes.json().catch(() => null)) as {
        success?: boolean;
        handle?: string;
        publicAccessToken?: string;
      } | null;

      if (enqueueRes.ok && enqueueData?.success && enqueueData.handle) {
        setState({
          content: "",
          isStreaming: false,
          error: null,
          isSandbox: false,
          queued: true,
          runHandle: enqueueData.handle,
          publicAccessToken: enqueueData.publicAccessToken ?? null,
        });
        return;
      }

      // Not configured / not authenticated / failed — fall through to SSE.
      console.warn(
        `[MealPlanStream] Enqueue route unavailable (${enqueueRes.status}) — falling back to direct SSE streaming.`,
        enqueueData,
      );
    } catch (err) {
      console.warn(
        "[MealPlanStream] Enqueue request failed — falling back to direct SSE streaming:",
        err,
      );
    }

    // ── Stage 2: direct SSE streaming (existing behavior) ─────────────
    try {
      const response = await fetch(`${apiBaseUrl}/api/ai/meal-plans/generate`, {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
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
            queued: false,
            runHandle: null,
            publicAccessToken: null,
          });
          return;
        }

        setState({
          content: "",
          isStreaming: false,
          error: `Access denied (${response.status}).`,
          isSandbox: false,
          queued: false,
          runHandle: null,
          publicAccessToken: null,
        });
        return;
      }

      if (!response.ok) {
        const bodyPreview = await response.text().catch(() => "");
        console.error(
          `[MealPlanStream] Request failed (${response.status} ${response.statusText}) → ${apiBaseUrl}/api/ai/meal-plans/generate`,
          bodyPreview || "(no response body)",
        );
        setState({
          content: "",
          isStreaming: false,
          error: `Request failed with status ${response.status}`,
          isSandbox: false,
          queued: false,
          runHandle: null,
          publicAccessToken: null,
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
          queued: false,
          runHandle: null,
          publicAccessToken: null,
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
      console.error(
        "[MealPlanStream] Fetch/stream error — check CORS, backend availability, and NEXT_PUBLIC_API_URL:",
        err,
      );
      setState({
        content: "",
        isStreaming: false,
        error: err instanceof Error ? err.message : "Stream failed.",
        isSandbox: false,
        queued: false,
        runHandle: null,
        publicAccessToken: null,
      });
    }
  }, []);

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState({
      content: "",
      isStreaming: false,
      error: null,
      isSandbox: false,
      queued: false,
      runHandle: null,
      publicAccessToken: null,
    });
  }, []);

  return { ...state, generate, abort, reset };
}