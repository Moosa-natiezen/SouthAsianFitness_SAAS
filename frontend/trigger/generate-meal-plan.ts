import { logger, task } from "@trigger.dev/sdk/v3";

/**
 * Payload for the background AI meal plan generation task.
 *
 * `user_id` identifies the user the plan is generated for (used for logging and
 * tracing — auth is passed separately via `sessionCookie`, never the user ID).
 * Optional: callers that only hold the session cookie (e.g. the web enqueue
 * route) can omit it; the worker logs it as "unknown".
 */
export type GenerateMealPlanPayload = {
  user_id?: string;
  target_calories?: number | null;
  protein_g?: number | null;
  dietary_preferences?: string[];
  allergies?: string[];
  cuisine_type?: string | null;
  /**
   * Session cookie (e.g. `saf_session=...`) from the authenticated request that
   * enqueued this task. The FastAPI backend authenticates via session cookies,
   * so the worker forwards it verbatim as the `Cookie` header.
   */
  sessionCookie?: string;
};

/**
 * Resolve the FastAPI backend base URL.
 * Order: TRIGGER_BACKEND_URL → NEXT_PUBLIC_API_URL → local dev default.
 */
function resolveBackendUrl(): string {
  const explicit = process.env.TRIGGER_BACKEND_URL;
  const nextPublic = process.env.NEXT_PUBLIC_API_URL;
  return (explicit ?? nextPublic ?? "http://localhost:8000").replace(/\/$/, "");
}

/**
 * Background task that runs the AI meal plan generation against our FastAPI
 * backend. This keeps long-running generation off the request/response path so
 * the frontend can poll for the result instead of holding an SSE connection.
 *
 * The backend endpoint returns a Server-Sent Events stream; we accumulate the
 * `data:` text chunks into a single markdown document and return it.
 */
export const generateMealPlanTask = task({
  id: "generate-meal-plan-task",
  // A single meal plan generation is a long-running job — allow up to 10 minutes.
  maxDuration: 600,
  run: async (payload: GenerateMealPlanPayload) => {
    const { user_id = "unknown", sessionCookie, ...generationParams } = payload;
    const backendUrl = resolveBackendUrl();

    logger.info("Starting AI meal plan generation", {
      user_id,
      target_calories: generationParams.target_calories,
      cuisine_type: generationParams.cuisine_type,
      dietary_preferences: generationParams.dietary_preferences,
      backend: backendUrl,
    });

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    };
    if (sessionCookie) {
      headers.Cookie = sessionCookie;
    }

    let response: Response;
    try {
      response = await fetch(`${backendUrl}/api/ai/meal-plans/generate`, {
        method: "POST",
        headers,
        body: JSON.stringify(generationParams),
      });
    } catch (err) {
      logger.error("Network error calling meal plan generation endpoint", {
        user_id,
        backend: backendUrl,
        error: err instanceof Error ? err.message : String(err),
      });
      throw new Error(
        `Failed to reach the meal plan generation backend at ${backendUrl}. ` +
          "Check TRIGGER_BACKEND_URL / NEXT_PUBLIC_API_URL and backend availability.",
      );
    }

    if (!response.ok) {
      const bodyPreview = await response.text().catch(() => "");
      logger.error("Meal plan generation endpoint returned an error status", {
        status: response.status,
        statusText: response.statusText,
        body: bodyPreview.slice(0, 500),
      });
      throw new Error(
        `Meal plan generation failed with status ${response.status} ${response.statusText}`,
      );
    }

    // The backend streams the plan as SSE (`data: {json}` records, `[DONE]` terminator).
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Meal plan generation returned an unreadable response body.");
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let markdown = "";
    let sawDone = false;

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const records = buffer.split("\n\n");
        buffer = records.pop() ?? "";

        for (const record of records) {
          for (const line of record.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6).trim();
            if (data === "[DONE]") {
              sawDone = true;
              break;
            }
            try {
              const parsed = JSON.parse(data) as { text?: string; error?: string };
              if (parsed.error) {
                logger.error("Meal plan generation stream reported an error", {
                  user_id,
                  error: parsed.error,
                });
                throw new Error(parsed.error);
              }
              if (parsed.text) markdown += parsed.text;
            } catch (err) {
              // Only surface real stream errors; skip unparseable keep-alive lines.
              if (err instanceof Error && err.message.startsWith("Meal plan generation stream")) {
                throw err;
              }
            }
          }
          if (sawDone) break;
        }
        if (sawDone) break;
      }
    } finally {
      reader.releaseLock();
    }

    if (!markdown) {
      throw new Error(
        "Meal plan generation completed without producing any content. " +
          (sawDone ? "" : "(stream ended without a [DONE] terminator) "),
      );
    }

    logger.info("Meal plan generation finished", {
      user_id,
      length: markdown.length,
      stream_terminated: sawDone,
    });

    return { user_id, markdown, stream_terminated: sawDone };
  },
});