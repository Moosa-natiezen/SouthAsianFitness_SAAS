import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { tasks } from "@trigger.dev/sdk/v3";

import type { MealPlanStreamRequest } from "@/hooks/use-meal-plan-stream";

/**
 * Enqueue an AI meal plan generation as a Trigger.dev background task.
 *
 * Returns the run handle immediately so the frontend doesn't have to hold an
 * SSE connection open for the whole generation. The background worker
 * (`trigger/generate-meal-plan.ts`) forwards the authenticated session cookie
 * to the FastAPI backend and accumulates the generated markdown.
 *
 * Graceful degradation: the background queue is an optional enhancement. When
 * it is not provisioned (env vars missing/placeholder) this endpoint returns
 * a structured 200 `{ success: false, reason: "queue_not_provisioned" }` —
 * NOT a 503 — so the client can quietly fall back to direct SSE streaming
 * without surfacing an error. Real enqueue failures still return 500.
 *
 * Requires:
 *  - `TRIGGER_PROJECT_ID` + `TRIGGER_SECRET_KEY` (from cloud.trigger.dev)
 *  - A valid `saf_session` cookie (same-origin in production via the Vercel
 *    rewrite proxy, so the worker can authenticate to the backend).
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const TRIGGER_UNCONFIGURED =
  !process.env.TRIGGER_PROJECT_ID ||
  process.env.TRIGGER_PROJECT_ID.startsWith("proj_replace") ||
  !process.env.TRIGGER_SECRET_KEY;

export async function POST(request: Request) {
  let body: MealPlanStreamRequest;
  try {
    body = (await request.json()) as MealPlanStreamRequest;
  } catch {
    return NextResponse.json(
      { success: false, error: "Invalid JSON body." },
      { status: 400 },
    );
  }

  if (TRIGGER_UNCONFIGURED) {
    // Expected operating state when the queue isn't provisioned yet — not a
    // server error. The client falls back to direct SSE streaming.
    return NextResponse.json({
      success: false,
      reason: "queue_not_provisioned",
      error: "Background queue is not configured; using direct streaming.",
    });
  }

  // The session token is opaque (server-side hashed), so we forward the raw
  // cookie value to the worker — the backend validates it, not us.
  const sessionCookie = (await cookies()).get("saf_session")?.value;
  if (!sessionCookie) {
    return NextResponse.json(
      { success: false, error: "Not authenticated — session cookie missing." },
      { status: 401 },
    );
  }

  try {
    const handle = await tasks.trigger("generate-meal-plan-task", {
      target_calories: body.target_calories ?? null,
      protein_g: body.protein_g ?? null,
      dietary_preferences: body.dietary_preferences ?? [],
      allergies: body.allergies ?? [],
      cuisine_type: body.cuisine_type ?? null,
      sessionCookie: `saf_session=${sessionCookie}`,
    });

    // `publicAccessToken` lets the browser subscribe to this run's realtime
    // updates via useRealtimeRun without exposing any secret key.
    return NextResponse.json({
      success: true,
      handle: handle.id,
      publicAccessToken: handle.publicAccessToken,
    });
  } catch (err) {
    // Log server-side with full detail; give the client a stable, non-leaky
    // message. The client treats any non-success as "use direct SSE".
    console.error("[MealPlanEnqueue] Failed to trigger background task:", err);
    return NextResponse.json(
      {
        success: false,
        reason: "enqueue_failed",
        error:
          err instanceof Error
            ? err.message
            : "Failed to enqueue meal plan task.",
      },
      { status: 500 },
    );
  }
}