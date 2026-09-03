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
      <div className="glass rounded-2xl p-6">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-orange-500">Today&apos;s Plan</p>
        <div className="mt-4 space-y-3">
          <Skeleton className="h-20 w-full rounded-xl bg-stone-100" />
          <Skeleton className="h-20 w-full rounded-xl bg-stone-100" />
          <Skeleton className="h-20 w-full rounded-xl bg-stone-100" />
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="glass rounded-2xl p-6">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-orange-500">Today&apos;s Plan</p>
        <AlertBanner variant="error" message={state.message} className="mt-4" />
        <Button variant="outline" size="sm" className="mt-3" onClick={fetchPlan}>
          Try again
        </Button>
      </div>
    );
  }

  if (state.status === "failure") {
    return (
      <div className="glass rounded-2xl p-6">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-orange-500">Today&apos;s Plan</p>
        <AlertBanner variant="warning" message={state.data.reason} className="mt-4" />
        {state.data.suggestions.length > 0 && (
          <ul className="mt-2 list-inside list-disc text-sm text-stone-500">
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
    <div className="glass rounded-2xl p-6 transition-all duration-300 hover:border-orange-200">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-orange-500">Today&apos;s Plan</p>
        <Link href="/dashboard/meal-plans" className="text-xs text-stone-400 hover:text-orange-600 transition-colors duration-300">
          View full plan →
        </Link>
      </div>
      <h2 className="mt-2 text-lg font-semibold text-stone-900">{plan.plan_name}</h2>

      {/* Meals */}
      <div className="mt-4 space-y-2">
        {day.meals.map((meal) => (
          <div key={meal.meal_type} className="glass rounded-xl p-4 transition-all duration-300 hover:bg-stone-50">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-stone-700">
                {mealEmoji[meal.meal_type] ?? "🍽️"}{" "}
                {meal.meal_type.charAt(0).toUpperCase() + meal.meal_type.slice(1)}
              </p>
              <p className="text-sm text-stone-500 tabular-nums">
                {Math.round(meal.subtotal_calories)} kcal
              </p>
            </div>
            <div className="mt-2.5 space-y-1">
              {meal.foods.map((food) => (
                <div key={food.food_id} className="flex items-center justify-between text-sm">
                  <span className="text-stone-600">
                    {food.name}{" "}
                    <span className="text-stone-400">
                      {food.serving_quantity > 0
                        ? `${food.serving_quantity}${food.serving_unit_code}`
                        : `${food.portion_grams}g`}
                    </span>
                  </span>
                  <span className="text-stone-400 tabular-nums">{Math.round(food.calories)} kcal</span>
                </div>
              ))}
            </div>
            <div className="mt-2.5 flex gap-3 text-xs">
              <span className="text-orange-500">P {Math.round(meal.subtotal_protein_g)}g</span>
              <span className="text-emerald-600">C {Math.round(meal.subtotal_carbs_g)}g</span>
              <span className="text-amber-600">F {Math.round(meal.subtotal_fat_g)}g</span>
            </div>
          </div>
        ))}
      </div>

      {/* Daily totals */}
      <div className="mt-4 glass rounded-xl p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-stone-700">Daily Total</p>
          <p className="text-sm font-semibold tabular-nums text-stone-900">{Math.round(day.total_calories)} kcal</p>
        </div>
        <div className="mt-2 flex gap-4 text-xs">
          <span className="text-orange-500 tabular-nums">Protein {Math.round(day.total_protein_g)}g</span>
          <span className="text-emerald-600 tabular-nums">Carbs {Math.round(day.total_carbs_g)}g</span>
          <span className="text-amber-600 tabular-nums">Fat {Math.round(day.total_fat_g)}g</span>
        </div>
        {plan.nutrition && (
          <p className="mt-2 text-xs text-stone-400">
            Target: {Math.round(plan.nutrition.calorie_target)} kcal
            ({Math.round(day.total_calories / plan.nutrition.calorie_target * 100)}%)
          </p>
        )}
      </div>
    </div>
  );
}
