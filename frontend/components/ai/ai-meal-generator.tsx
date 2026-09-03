"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { useMealPlanStream } from "@/hooks/use-meal-plan-stream";
import { saveAiMealPlan } from "@/lib/api";

/**
 * AI Meal Plan Generator with live Markdown streaming.
 * Dark luxury glass aesthetic with glowing cursor animation.
 */
export function AiMealGenerator() {
  const { content, isStreaming, error, isSandbox, generate, reset } =
    useMealPlanStream();

  const [targetCalories, setTargetCalories] = useState("");
  const [proteinG, setProteinG] = useState("");
  const [cuisineType, setCuisineType] = useState("South Asian");

  const [saveLoading, setSaveLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{
    type: "info" | "error";
    text: string;
  } | null>(null);

  const handleSave = async () => {
    if (!content) return;
    setSaveLoading(true);
    setSaveMsg(null);
    try {
      await saveAiMealPlan({
        title: cuisineType ? `${cuisineType} AI Plan` : "AI Meal Plan",
        content,
        target_calories: targetCalories ? Number(targetCalories) : undefined,
        protein_g: proteinG ? Number(proteinG) : undefined,
      });
      setSaveMsg({ type: "info", text: "Plan saved successfully!" });
    } catch (err: unknown) {
      setSaveMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to save plan.",
      });
    } finally {
      setSaveLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveMsg(null);
    generate({
      target_calories: targetCalories ? Number(targetCalories) : undefined,
      protein_g: proteinG ? Number(proteinG) : undefined,
      cuisine_type: cuisineType || undefined,
    });
  };

  return (
    <div className="space-y-5">
      {/* ── Form ─────────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-2xl glass p-6">
        <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-emerald-700/5 blur-[40px]" />
        <div className="absolute -left-10 -bottom-10 h-32 w-32 rounded-full bg-emerald-600/5 blur-[40px]" />

        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-600">
            AI Meal Plan Studio
          </p>
          <h3 className="mt-2 text-lg font-semibold text-stone-900 dark:text-zinc-100">
            Generate with AI
          </h3>
          <p className="mt-1 text-sm text-stone-500 dark:text-zinc-500">
            Set your targets and let AI create a personalized meal plan.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <InputField
                id="ai-calories"
                label="Target Calories"
                placeholder="e.g. 2200"
                type="number"
                min={500}
                max={10000}
                value={targetCalories}
                onChange={setTargetCalories}
                disabled={isStreaming}
              />
              <InputField
                id="ai-protein"
                label="Protein (g)"
                placeholder="e.g. 120"
                type="number"
                min={0}
                max={500}
                value={proteinG}
                onChange={setProteinG}
                disabled={isStreaming}
              />
              <InputField
                id="ai-cuisine"
                label="Cuisine"
                placeholder="e.g. South Asian"
                type="text"
                value={cuisineType}
                onChange={setCuisineType}
                disabled={isStreaming}
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={isStreaming}
                className="btn-chrome-accent rounded-xl px-6 py-3 text-sm font-semibold disabled:opacity-50"
              >
                {isStreaming ? (
                  <span className="flex items-center gap-2">
                    <Spinner />
                    Generating…
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                    </svg>
                    Generate AI Plan
                  </span>
                )}
              </button>

              {(content || error) && (
                <button
                  type="button"
                  onClick={reset}
                  disabled={isStreaming}
                  className="rounded-xl border border-stone-200 dark:border-zinc-700 bg-stone-50 dark:bg-zinc-800 px-5 py-3 text-sm font-medium text-stone-500 dark:text-zinc-500 transition-all hover:bg-stone-50 dark:bg-zinc-800 hover:text-stone-900 dark:text-zinc-100 disabled:opacity-50"
                >
                  Clear
                </button>
              )}
            </div>
          </form>
        </div>
      </div>

      {/* ── Sandbox Banner ──────────────────────────────────────────────── */}
      {isSandbox && (
        <div className="rounded-2xl border border-[#F59E0B]/20 bg-[#F59E0B]/5 px-4 py-3">
          <p className="flex items-center gap-2 text-sm font-medium text-[#F59E0B]">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#F59E0B]" />
            Using offline AI model (Sandbox mode) — add OPENAI_API_KEY for live generation
          </p>
        </div>
      )}

      {/* ── Error ─────────────────────────────────────────────────────── */}
      {error && !isSandbox && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4">
          <p className="text-sm font-medium text-red-300">{error}</p>
        </div>
      )}

      {/* ── Streaming Output ──────────────────────────────────────────── */}
      {(content || isStreaming) && (
        <div className="relative overflow-hidden rounded-2xl glass p-6">
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-emerald-700/5 blur-[40px]" />

          <div className="relative">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-600">
                  AI Generated Plan
                </p>
                {isStreaming && (
                  <span className="flex items-center gap-1.5 rounded-full bg-white dark:bg-zinc-900/10 px-2.5 py-1 text-[10px] font-semibold text-stone-600">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white dark:bg-zinc-900 shadow-[0_0_6px_rgba(16,185,129,0.8)]" />
                    Streaming
                  </span>
                )}
              </div>
            </div>

            {/* Markdown content with streaming cursor */}
            <div className={`prose prose-sm prose-invert prose-zinc max-w-none ${isStreaming ? "streaming-cursor" : ""}`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </div>

            {/* Loading dots */}
            {isStreaming && (
              <div className="mt-4 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white dark:bg-zinc-900 [animation-delay:0ms]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white dark:bg-zinc-900 [animation-delay:150ms]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white dark:bg-zinc-900 [animation-delay:300ms]" />
              </div>
            )}

            {/* Action toolbar — shown when streaming is done */}
            {!isStreaming && content && (
              <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-stone-200 dark:border-zinc-700 pt-4">
                <button
                  onClick={handleSave}
                  disabled={saveLoading}
                  className="flex items-center gap-2 rounded-xl bg-white dark:bg-zinc-900/10 border border-stone-300 px-4 py-2.5 text-sm font-medium text-stone-600 transition-all hover:bg-stone-50 dark:bg-zinc-800 disabled:opacity-50"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
                  </svg>
                  {saveLoading ? "Saving…" : "Save to My Plans"}
                </button>

                <button
                  onClick={() => {
                    navigator.clipboard.writeText(content);
                  }}
                  className="flex items-center gap-2 rounded-xl border border-stone-200 dark:border-zinc-700 bg-stone-50 dark:bg-zinc-800 px-4 py-2.5 text-sm font-medium text-stone-500 dark:text-zinc-500 transition-all hover:bg-stone-50 dark:bg-zinc-800 hover:text-stone-900 dark:text-zinc-100"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                  Copy Plan
                </button>

                <button
                  onClick={() => {
                    reset();
                    generate({
                      target_calories: targetCalories ? Number(targetCalories) : undefined,
                      protein_g: proteinG ? Number(proteinG) : undefined,
                      cuisine_type: cuisineType || undefined,
                    });
                  }}
                  className="flex items-center gap-2 rounded-xl border border-stone-200 dark:border-zinc-700 bg-stone-50 dark:bg-zinc-800 px-4 py-2.5 text-sm font-medium text-stone-500 dark:text-zinc-500 transition-all hover:bg-stone-50 dark:bg-zinc-800 hover:text-stone-900 dark:text-zinc-100"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                  </svg>
                  Regenerate
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Save notification */}
      {saveMsg && (
        <AlertBanner variant={saveMsg.type} message={saveMsg.text} />
      )}

      {/* ── Empty State ───────────────────────────────────────────────── */}
      {!content && !isStreaming && !error && (
        <div className="rounded-2xl border border-dashed border-stone-200 dark:border-zinc-700 bg-white dark:bg-zinc-900/[0.02] p-10 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-white dark:bg-zinc-900/10">
            <svg className="h-6 w-6 text-stone-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
          </div>
          <p className="mt-4 text-sm text-stone-500 dark:text-zinc-500">
            Set your preferences above and click &quot;Generate AI Plan&quot; to get a
            personalized plan powered by AI.
          </p>
        </div>
      )}
    </div>
  );
}

/* ── Input Field ─────────────────────────────────────────────────────── */

function InputField({
  id,
  label,
  type,
  placeholder,
  value,
  onChange,
  disabled,
  min,
  max,
}: {
  id: string;
  label: string;
  type: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  disabled: boolean;
  min?: number;
  max?: number;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-xs font-medium text-stone-500 dark:text-zinc-500">
        {label}
      </label>
      <input
        id={id}
        type={type}
        min={min}
        max={max}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full rounded-xl border border-stone-200 dark:border-zinc-700 bg-stone-50 dark:bg-zinc-800 px-3.5 py-2.5 text-sm text-stone-900 dark:text-zinc-100 placeholder:text-stone-500 dark:text-zinc-500 transition-all focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600/30 disabled:opacity-50"
      />
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
