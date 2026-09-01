"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  generateMealPlan,
  getTodaysMealPlan,
  type GeneratedDay,
  type MealPlanFailure,
  type MealPlanResponse,
} from "@/lib/api";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; plan: MealPlanResponse; day: GeneratedDay }
  | { status: "failure"; data: MealPlanFailure }
  | { status: "error"; message: string };

const mealEmoji: Record<string, string> = {
  breakfast: "🍳",
  lunch: "🍛",
  snack: "🥗",
  dinner: "🍲",
};

export function TodayPlanCard() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  const fetchPlan = () => {
    setState({ status: "loading" });
    getTodaysMealPlan()
      .then((existingPlan) => {
        if (existingPlan) {
          setState({ status: "ready", plan: existingPlan, day: existingPlan.days[0] });
          return;
        }
        // No existing plan — generate a new one
        return generateMealPlan(1, 4).then((result) => {
          if ("success" in result && !result.success) {
            setState({ status: "failure", data: result as MealPlanFailure });
          } else {
            const plan = result as MealPlanResponse;
            setState({ status: "ready", plan, day: plan.days[0] });
          }
        });
      })
      .catch((err: unknown) => {
        setState({
          status: "error",
          message: err instanceof Error ? err.message : "Failed to load meal plan.",
        });
      });
  };

  useEffect(() => {
    fetchPlan();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (state.status === "loading") {
    return (
      <div className="rounded-2xl glass p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#FF4060]">
          Today&apos;s Plan
        </p>
        <div className="mt-4 space-y-3">
          <Skeleton className="h-20 w-full rounded-xl bg-white/4" />
          <Skeleton className="h-20 w-full rounded-xl bg-white/4" />
          <Skeleton className="h-20 w-full rounded-xl bg-white/4" />
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="rounded-2xl glass p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#FF4060]">
          Today&apos;s Plan
        </p>
        <AlertBanner variant="error" message={state.message} className="mt-4" />
        <Button variant="outline" size="sm" className="mt-3" onClick={fetchPlan}>
          Try again
        </Button>
      </div>
    );
  }

  if (state.status === "failure") {
    return (
      <div className="rounded-2xl glass p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#FF4060]">
          Today&apos;s Plan
        </p>
        <AlertBanner variant="warning" message={state.data.reason} className="mt-4" />
        {state.data.suggestions.length > 0 && (
          <ul className="mt-2 list-inside list-disc text-sm text-[#8A8A94]">
            {state.data.suggestions.map((s, i) => (<li key={i}>{s}</li>))}
          </ul>
        )}
        <Button variant="outline" size="sm" className="mt-3" onClick={fetchPlan}>
          Try again
        </Button>
      </div>
    );
  }

  const { plan, day } = state;

  return (
    <div className="rounded-2xl glass p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#FF4060]">
            Today&apos;s Plan
          </p>
          <h2 className="mt-1 text-lg font-semibold text-white">{plan.plan_name}</h2>
        </div>
        <Link href="/dashboard/meal-plans">
          <Button variant="outline" size="sm">View full plan</Button>
        </Link>
      </div>

      {/* Meals */}
      <div className="mt-4 space-y-3">
        {day.meals.map((meal) => (
          <div key={meal.meal_type} className="rounded-xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between">
              <p className="font-medium text-[#E8E8EC]">
                {mealEmoji[meal.meal_type] ?? "🍽️"}{" "}
                {meal.meal_type.charAt(0).toUpperCase() + meal.meal_type.slice(1)}
              </p>
              <p className="text-sm text-[#8A8A94]">
                {Math.round(meal.subtotal_calories)} kcal
              </p>
            </div>
            <div className="mt-2 space-y-1">
              {meal.foods.map((food) => (
                <div key={food.food_id} className="flex items-center justify-between text-sm">
                  <span className="text-[#C4C4CC]">
                    {food.name}{" "}
                    <span className="text-[#8A8A94]">
                      {food.serving_quantity > 0
                        ? `${food.serving_quantity}${food.serving_unit_code}`
                        : `${food.portion_grams}g`}
                    </span>
                  </span>
                  <span className="text-[#8A8A94]">{Math.round(food.calories)} kcal</span>
                </div>
              ))}
            </div>
            <div className="mt-2 flex gap-3 text-xs text-[#8A8A94]">
              <span>P {Math.round(meal.subtotal_protein_g)}g</span>
              <span>C {Math.round(meal.subtotal_carbs_g)}g</span>
              <span>F {Math.round(meal.subtotal_fat_g)}g</span>
            </div>
          </div>
        ))}
      </div>

      {/* Daily totals */}
      <div className="mt-4 rounded-xl border border-[#DC143C]/20 bg-[#DC143C]/5 p-4">
        <div className="flex items-center justify-between">
          <p className="font-medium text-[#DC143C]">Daily Total</p>
          <p className="font-semibold text-[#DC143C]">{Math.round(day.total_calories)} kcal</p>
        </div>
        <div className="mt-1 flex gap-4 text-sm text-[#DC143C]">
          <span>Protein {Math.round(day.total_protein_g)}g</span>
          <span>Carbs {Math.round(day.total_carbs_g)}g</span>
          <span>Fat {Math.round(day.total_fat_g)}g</span>
        </div>
        {plan.nutrition && (
          <p className="mt-1 text-xs text-[#DC143C]">
            Target: {Math.round(plan.nutrition.calorie_target)} kcal
            ({Math.round(day.total_calories / plan.nutrition.calorie_target * 100)}%)
          </p>
        )}
      </div>

      {/* Warnings */}
      {day.warnings.length > 0 && (
        <div className="mt-3 space-y-1">
          {day.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-600">⚠ {w}</p>
          ))}
        </div>
      )}

      {plan.warnings.length > 0 && (
        <div className="mt-3 space-y-1">
          {plan.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-600">⚠ {w}</p>
          ))}
        </div>
      )}
    </div>
  );
}
