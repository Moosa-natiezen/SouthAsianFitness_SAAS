"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useMealPlanStream } from "@/hooks/use-meal-plan-stream";

/**
 * AI Meal Plan Generator with live Markdown streaming.
 *
 * Sends user preferences to the streaming backend endpoint and
 * renders the AI-generated meal plan as Markdown in real time.
 */
export function AiMealGenerator() {
  const { content, isStreaming, error, generate, reset } =
    useMealPlanStream();

  const [targetCalories, setTargetCalories] = useState<string>("");
  const [proteinG, setProteinG] = useState<string>("");
  const [cuisineType, setCuisineType] = useState("South Asian");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    generate({
      target_calories: targetCalories ? Number(targetCalories) : undefined,
      protein_g: proteinG ? Number(proteinG) : undefined,
      cuisine_type: cuisineType || undefined,
    });
  };

  return (
    <div className="space-y-4">
      {/* ── Form ─────────────────────────────────────────────────────── */}
      <Card>
        <CardContent className="pt-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              {/* Target Calories */}
              <div className="space-y-1.5">
                <label
                  htmlFor="ai-calories"
                  className="text-sm font-medium text-slate-700"
                >
                  Target Calories
                </label>
                <input
                  id="ai-calories"
                  type="number"
                  min={500}
                  max={10000}
                  placeholder="e.g. 2200"
                  value={targetCalories}
                  onChange={(e) => setTargetCalories(e.target.value)}
                  disabled={isStreaming}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
                />
              </div>

              {/* Protein */}
              <div className="space-y-1.5">
                <label
                  htmlFor="ai-protein"
                  className="text-sm font-medium text-slate-700"
                >
                  Protein (g)
                </label>
                <input
                  id="ai-protein"
                  type="number"
                  min={0}
                  max={500}
                  placeholder="e.g. 120"
                  value={proteinG}
                  onChange={(e) => setProteinG(e.target.value)}
                  disabled={isStreaming}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
                />
              </div>

              {/* Cuisine Type */}
              <div className="space-y-1.5">
                <label
                  htmlFor="ai-cuisine"
                  className="text-sm font-medium text-slate-700"
                >
                  Cuisine
                </label>
                <input
                  id="ai-cuisine"
                  type="text"
                  placeholder="e.g. South Asian"
                  value={cuisineType}
                  onChange={(e) => setCuisineType(e.target.value)}
                  disabled={isStreaming}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={isStreaming}
                size="lg"
              >
                {isStreaming ? (
                  <span className="flex items-center gap-2">
                    <Spinner />
                    Generating...
                  </span>
                ) : (
                  "Generate AI Meal Plan"
                )}
              </Button>

              {(content || error) && (
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  onClick={reset}
                  disabled={isStreaming}
                >
                  Clear
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* ── Error ─────────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">{error}</p>
        </div>
      )}

      {/* ── Streaming Output ──────────────────────────────────────────── */}
      {(content || isStreaming) && (
        <Card>
          <CardContent className="pt-4">
            <div className="mb-3 flex items-center gap-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                AI Generated Meal Plan
              </p>
              {isStreaming && (
                <span className="flex items-center gap-1 text-xs text-emerald-600">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                  Streaming
                </span>
              )}
            </div>

            <div className="prose prose-sm prose-slate max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </div>

            {isStreaming && (
              <div className="mt-3 flex items-center gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:0ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:150ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-400 [animation-delay:300ms]" />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Empty State ───────────────────────────────────────────────── */}
      {!content && !isStreaming && !error && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-sm text-slate-500">
            Fill in your preferences above and click &quot;Generate AI Meal
            Plan&quot; to get a personalized plan powered by AI.
          </p>
        </div>
      )}
    </div>
  );
}

/* ── Spinner ──────────────────────────────────────────────────────────── */

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
