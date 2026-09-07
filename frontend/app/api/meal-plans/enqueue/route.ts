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
 * Requires:
 *  - `TRIGGER_PROJECT_ID` (project ref from cloud.trigger.dev)
 *  - A valid `saf_session` cookie (same-origin in production via the Vercel
 *    rewrite proxy, so the worker can authenticate to the backend).
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const TRIGGER_UNCONFIGURED =
  !process.env.TRIGGER_PROJECT_ID ||
  process.env.TRIGGER_PROJECT_ID.startsWith("proj_replace");

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
    return NextResponse.json(
      {
        success: false,
        error: "Trigger.dev is not configured (TRIGGER_PROJECT_ID is not set).",
      },
      { status: 503 },
    );
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

    return NextResponse.json({ success: true, handle: handle.id });
  } catch (err) {
    console.error("[MealPlanEnqueue] Failed to trigger background task:", err);
    return NextResponse.json(
      {
        success: false,
        error:
          err instanceof Error
            ? err.message
            : "Failed to enqueue meal plan task.",
      },
      { status: 500 },
    );
  }
}