"use client";

import { useEffect, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { MealPlanView } from "@/components/meal-plan/meal-plan-view";
import {
  generateMealPlan,
  getTodaysMealPlan,
  type MealPlanFailure,
  type MealPlanResponse,
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

  // On mount, try to load today's existing plan
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
  }, []);

  const handleGenerate = async () => {
    setState({ status: "loading" });
    try {
      const result = await generateMealPlan(planDays, mealCount);
      if ("success" in result && !result.success) {
        setState({ status: "failure", data: result as MealPlanFailure });
      } else {
        setState({ status: "ready", plan: result as MealPlanResponse });
      }
    } catch (err: unknown) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to generate meal plan.",
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
          Meal Plans
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">Generate Your Plan</h1>
        <p className="mt-2 text-slate-600">
          Create a personalized meal plan based on your nutrition targets and food preferences.
        </p>

        {/* Controls */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Number of days</label>
            <div className="flex flex-wrap gap-2">
              {dayOptions.map((d) => (
                <button
                  key={d}
                  onClick={() => setPlanDays(d)}
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                    planDays === d
                      ? "border-emerald-600 bg-emerald-50 text-emerald-700"
                      : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                  aria-pressed={planDays === d}
                >
                  {d} {d === 1 ? "day" : "days"}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Meals per day</label>
            <div className="flex flex-wrap gap-2">
              {mealOptions.map((m) => (
                <button
                  key={m}
                  onClick={() => setMealCount(m)}
                  className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                    mealCount === m
                      ? "border-emerald-600 bg-emerald-50 text-emerald-700"
                      : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
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
          {state.status === "loading" ? "Generating..." : "Generate Plan"}
        </Button>
      </div>

      {/* Loading */}
      {state.status === "loading" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" aria-live="polite">
          <p className="text-center text-slate-600">Generating your personalized plan...</p>
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <AlertBanner variant="error" message={state.message} />
      )}

      {/* Failure */}
      {state.status === "failure" && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6">
          <h3 className="font-semibold text-amber-800">Could not generate plan</h3>
          <p className="mt-1 text-sm text-amber-700">{state.data.reason}</p>
          {state.data.conflict_details.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-sm text-amber-700">
              {state.data.conflict_details.map((d, i) => (<li key={i}>{d}</li>))}
            </ul>
          )}
          {state.data.suggestions.length > 0 && (
            <div className="mt-3">
              <p className="text-sm font-medium text-amber-800">Suggestions:</p>
              <ul className="mt-1 list-inside list-disc text-sm text-amber-700">
                {state.data.suggestions.map((s, i) => (<li key={i}>{s}</li>))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Idle state - helpful guidance */}
      {state.status === "idle" && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-lg font-medium text-slate-700">No meal plan yet</p>
          <p className="mt-2 text-slate-500">
            Select your preferences above and click &quot;Generate Plan&quot; to create
            a personalized meal plan based on your nutrition targets.
          </p>
        </div>
      )}

      {/* Plan display */}
      {state.status === "ready" && (
        <MealPlanView plan={state.plan} />
      )}
    </div>
  );
}
