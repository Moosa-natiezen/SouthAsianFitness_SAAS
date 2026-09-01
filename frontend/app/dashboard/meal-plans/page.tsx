"use client";

import { useEffect, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AiMealGenerator } from "@/components/ai/ai-meal-generator";
import { MealPlanView } from "@/components/meal-plan/meal-plan-view";
import {
  createCheckoutSession,
  deleteMealPlan,
  generateMealPlan,
  getTodaysMealPlan,
  listMealPlans,
  type MealPlanFailure,
  type MealPlanListResponse,
  type MealPlanResponse,
  type MealPlanSummary,
} from "@/lib/api";

type PlanState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; plan: MealPlanResponse }
  | { status: "failure"; data: MealPlanFailure }
  | { status: "error"; message: string };

const dayOptions = [1, 3, 7, 14, 30];
const mealOptions = [2, 3, 4, 6];

export default function MealPlansPage() {
  const [planDays, setPlanDays] = useState(1);
  const [mealCount, setMealCount] = useState(4);
  const [state, setState] = useState<PlanState>({ status: "idle" });

  /* ── Plan history state ──────────────────────────────────────────── */
  const [history, setHistory] = useState<MealPlanListResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleteMsg, setDeleteMsg] = useState<{
    type: "info" | "error";
    text: string;
  } | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"optimizer" | "ai">("optimizer");

  /* ── Load today's plan + history ─────────────────────────────────── */

  const fetchHistory = () => {
    setHistoryLoading(true);
    listMealPlans({ limit: 20 })
      .then(setHistory)
      .catch((err: unknown) => {
        setHistoryError(
          err instanceof Error ? err.message : "Failed to load plan history.",
        );
      })
      .finally(() => setHistoryLoading(false));
  };

  useEffect(() => {
    setState({ status: "loading" });
    getTodaysMealPlan()
      .then((plan) => {
        if (plan) {
          setState({ status: "ready", plan });
        } else {
          setState({ status: "idle" });
        }
      })
      .catch(() => {
        setState({ status: "idle" });
      });
    fetchHistory();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Generate handler ────────────────────────────────────────────── */

  const handleGenerate = async () => {
    setState({ status: "loading" });
    try {
      const result = await generateMealPlan(planDays, mealCount);
      if ("success" in result && !result.success) {
        setState({ status: "failure", data: result as MealPlanFailure });
      } else {
        setState({ status: "ready", plan: result as MealPlanResponse });
        fetchHistory(); // refresh history after generating
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate meal plan.";
      if (msg.includes("Free tier limit reached")) {
        setShowPaywall(true);
      } else {
        setState({ status: "error", message: msg });
      }
    }
  };

  /* ── Delete handler ──────────────────────────────────────────────── */

  const handleUpgrade = async () => {
    setCheckoutLoading(true);
    try {
      const result = await createCheckoutSession();
      window.location.href = result.checkout_url;
    } catch (err: unknown) {
      setDeleteMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to start checkout.",
      });
      setCheckoutLoading(false);
    }
  };

  const handleDelete = async (planId: string) => {
    setDeleteId(planId);
    setDeleteMsg(null);
    try {
      await deleteMealPlan(planId);
      setDeleteMsg({ type: "info", text: "Plan deleted." });
      fetchHistory();
    } catch (err: unknown) {
      setDeleteMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to delete plan.",
      });
    } finally {
      setDeleteId(null);
    }
  };

  /* ── Render ──────────────────────────────────────────────────────── */

  return (
    <div className="space-y-6">
      {/* Tab switcher */}
      <div className="rounded-2xl glass p-6">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-[#c4854c]">
          Meal Plans
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-white">
          Generate Your Plan
        </h1>
        <p className="mt-2 text-zinc-400">
          Create a personalized meal plan using our optimizer or AI assistant.
        </p>

        <div className="mt-6 flex gap-2">
          <button
            onClick={() => setActiveTab("optimizer")}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
              activeTab === "optimizer"
                ? "border-[#c4854c]/30 bg-[#c4854c]/10 text-[#d4a574]"
                : "border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:bg-white/[0.06]"
            }`}
          >
            Deterministic Optimizer
          </button>
          <button
            onClick={() => setActiveTab("ai")}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
              activeTab === "ai"
                ? "border-[#c4854c]/30 bg-[#c4854c]/10 text-[#d4a574]"
                : "border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:bg-white/[0.06]"
            }`}
          >
            AI Generator ✨
          </button>
        </div>
      </div>

      {/* AI Generator Tab */}
      {activeTab === "ai" && <AiMealGenerator />}

      {/* Optimizer Tab */}
      {activeTab === "optimizer" && (
        <>
          <div className="rounded-2xl glass p-6">
        <h1 className="text-xl font-semibold text-white">
          {state.status === "ready" ? "Your Plan" : "Optimizer Plan"}
        </h1>
        <p className="mt-2 text-zinc-400">
          {state.status === "ready"
            ? "View your current plan or generate a new one."
            : "Generate a structured plan based on your nutrition targets and food database."}
        </p>

        {/* Controls */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-300">
              Number of days
            </label>
            <div className="flex flex-wrap gap-2">
              {dayOptions.map((d) => (
                <button
                  key={d}
                  onClick={() => setPlanDays(d)}
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                    planDays === d
                      ? "border-[#c4854c]/30 bg-[#c4854c]/10 text-[#d4a574]"
                      : "border-white/[0.08] bg-white/[0.03] text-zinc-300 hover:bg-white/[0.06]"
                  }`}
                  aria-pressed={planDays === d}
                >
                  {d} {d === 1 ? "day" : "days"}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-300">
              Meals per day
            </label>
            <div className="flex flex-wrap gap-2">
              {mealOptions.map((m) => (
                <button
                  key={m}
                  onClick={() => setMealCount(m)}
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                    mealCount === m
                      ? "border-[#c4854c]/30 bg-[#c4854c]/10 text-[#d4a574]"
                      : "border-white/[0.08] bg-white/[0.03] text-zinc-300 hover:bg-white/[0.06]"
                  }`}
                  aria-pressed={mealCount === m}
                >
                  {m} meals
                </button>
              ))}
            </div>
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          disabled={state.status === "loading"}
          className="mt-6"
          size="lg"
        >
          {state.status === "loading"
            ? "Generating..."
            : state.status === "ready"
              ? "Regenerate Plan"
              : "Generate Plan"}
        </Button>
      </div>

      {/* Loading */}
      {state.status === "loading" && (
        <div
          className="rounded-2xl glass p-6"
          aria-live="polite"
        >
          <p className="text-center text-zinc-400">
            Generating your personalized plan...
          </p>
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <AlertBanner variant="error" message={state.message} />
      )}

      {/* Failure */}
      {state.status === "failure" && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6">
          <h3 className="font-semibold text-amber-800">
            Could not generate plan
          </h3>
          <p className="mt-1 text-sm text-amber-700">{state.data.reason}</p>
          {state.data.conflict_details.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-sm text-amber-700">
              {state.data.conflict_details.map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
          )}
          {state.data.suggestions.length > 0 && (
            <div className="mt-3">
              <p className="text-sm font-medium text-amber-800">
                Suggestions:
              </p>
              <ul className="mt-1 list-inside list-disc text-sm text-amber-700">
                {state.data.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Paywall / Upgrade */}
      {showPaywall && (
        <div className="rounded-2xl border border-[#c4854c]/20 bg-[#c4854c]/5 p-8 text-center shadow-sm">
          <p className="text-lg font-semibold text-[#c4854c]">
            You've reached your limit
          </p>
          <p className="mt-2 text-[#c4854c]">
            Free users can generate up to 3 meal plans per month.
            Upgrade to Pro for unlimited generation.
          </p>
          <Button
            onClick={handleUpgrade}
            disabled={checkoutLoading}
            className="mt-4"
            size="lg"
          >
            {checkoutLoading ? "Loading..." : "Upgrade to Pro"}
          </Button>
        </div>
      )}

      {/* Idle state */}
      {state.status === "idle" && !showPaywall && (
        <div className="rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.01] p-8 text-center">
          <p className="text-lg font-medium text-zinc-300">No meal plan yet</p>
          <p className="mt-2 text-zinc-500">
            Select your preferences above and click &quot;Generate Plan&quot; to
            create a personalized meal plan.
          </p>
        </div>
      )}

          {/* Current plan display */}
          {state.status === "ready" && <MealPlanView plan={state.plan} />}
        </>
      )}

      {/* Delete notification */}
      {deleteMsg && (
        <AlertBanner variant={deleteMsg.type} message={deleteMsg.text} />
      )}

      {/* ── Plan History ──────────────────────────────────────────── */}
      <div className="rounded-2xl glass p-6">
        <h2 className="text-lg font-semibold text-white">
          Plan History
        </h2>
        <p className="mt-1 text-sm text-zinc-500">
          Your previously generated meal plans.
        </p>

        {historyLoading && (
          <div className="mt-4 space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        )}

        {historyError && (
          <AlertBanner variant="error" message={historyError} className="mt-4" />
        )}

        {!historyLoading && history && history.items.length === 0 && (
          <p className="mt-4 text-sm text-zinc-500">
            No meal plans generated yet.
          </p>
        )}

        {!historyLoading && history && history.items.length > 0 && (
          <div className="mt-4 space-y-3">
            {history.items.map((plan) => (
              <PlanHistoryCard
                key={plan.id}
                plan={plan}
                onDelete={handleDelete}
                deleting={deleteId === plan.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Plan History Card ──────────────────────────────────────────────── */

function PlanHistoryCard({
  plan,
  onDelete,
  deleting,
}: {
  plan: MealPlanSummary;
  onDelete: (id: string) => void;
  deleting: boolean;
}) {
  const createdDate = formatDate(plan.created_at);
  const dateRange = `${plan.start_date} → ${plan.end_date}`;

  return (
    <Card className="py-3">
      <CardContent className="flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-semibold text-white">
              {plan.name || "Meal Plan"}
            </h3>
            <Badge variant="secondary" className="shrink-0 text-xs">
              {plan.day_count} {plan.day_count === 1 ? "day" : "days"}
            </Badge>
          </div>
          <p className="mt-0.5 text-xs text-zinc-500">
            {dateRange}
            {plan.calorie_target != null && (
              <> · {Math.round(plan.calorie_target)} kcal/day</>
            )}
          </p>
          <p className="mt-0.5 text-xs text-zinc-500">
            Created {createdDate}
          </p>
        </div>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => onDelete(plan.id)}
          disabled={deleting}
        >
          {deleting ? "..." : "Delete"}
        </Button>
      </CardContent>
    </Card>
  );
}

/* ── Helpers ──────────────────────────────────────────────────────────── */

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}
