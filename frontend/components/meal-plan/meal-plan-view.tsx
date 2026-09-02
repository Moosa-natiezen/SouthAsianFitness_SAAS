"use client";

import { useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { MealCard } from "@/components/meal-plan/meal-card";
import type { GeneratedDay, MealPlanResponse } from "@/lib/api";

type MealPlanViewProps = {
  plan: MealPlanResponse;
};

export function MealPlanView({ plan }: MealPlanViewProps) {
  const [selectedDay, setSelectedDay] = useState(0);
  const day: GeneratedDay | undefined = plan.days[selectedDay];
  const hasMultipleDays = plan.days.length > 1;

  if (!day) {
    return <AlertBanner variant="warning" message="No days in this plan." />;
  }

  return (
    <div className="space-y-4">
      {/* Plan header */}
      <div className="rounded-2xl border border-white/10 bg-zinc-900/50 p-6 backdrop-blur-xl">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-zinc-400">
          Generated Plan
        </p>
        <h2 className="mt-1 text-xl font-semibold text-white">{plan.plan_name}</h2>
        <p className="mt-1 text-sm text-zinc-400">
          {plan.start_date} → {plan.end_date}
          {" · "}
          {plan.days.length} {plan.days.length === 1 ? "day" : "days"}
        </p>
      </div>

      {/* Day selector for multi-day plans */}
      {hasMultipleDays && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
          <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Select day">
            {plan.days.map((d, i) => (
              <button
                key={d.plan_date}
                role="tab"
                aria-selected={i === selectedDay}
                onClick={() => setSelectedDay(i)}
                className={`flex-shrink-0 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                  i === selectedDay
                    ? "border-white/20 bg-white/8 text-white"
                    : "border-white/10 bg-white/[0.04] text-zinc-400 hover:bg-white/[0.05]"
                }`}
              >
                <span className="block">Day {i + 1}</span>
                <span className="block text-xs text-zinc-400">{formatDate(d.plan_date)}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Day summary */}
      <DaySummary day={day} nutrition={plan.nutrition} currency={plan.budget.currency_code} />

      {/* Meals */}
      <div className="space-y-3">
        {day.meals.map((meal) => (
          <MealCard key={meal.meal_type} meal={meal} currency={plan.budget.currency_code} />
        ))}
      </div>

      {/* Day warnings */}
      {day.warnings.length > 0 && (
        <div className="space-y-2">
          {day.warnings.map((w, i) => (
            <AlertBanner key={i} variant="warning" message={w} />
          ))}
        </div>
      )}

      {/* Plan-level warnings */}
      {plan.warnings.length > 0 && (
        <div className="space-y-2">
          {plan.warnings.map((w, i) => (
            <AlertBanner key={`plan-${i}`} variant="info" message={w} />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Day summary ──────────────────────────────────────────────────────── */

function DaySummary({
  day,
  nutrition,
  currency,
}: {
  day: GeneratedDay;
  nutrition: MealPlanResponse["nutrition"];
  currency: string | null;
}) {
  const calPct = nutrition.calorie_target > 0
    ? Math.round((day.total_calories / nutrition.calorie_target) * 100)
    : 0;

  return (
    <div className="rounded-2xl border border-white/10 bg-zinc-900/50 p-5 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white">Daily Totals</h3>
        <span className="text-sm text-zinc-300">
          {Math.round(day.total_calories)} / {Math.round(nutrition.calorie_target)} kcal ({calPct}%)
        </span>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-3">
        <MacroBar label="Protein" actual={day.total_protein_g} target={nutrition.protein_g} unit="g" color="protein" />
        <MacroBar label="Carbs" actual={day.total_carbs_g} target={nutrition.carbs_g} unit="g" color="carbs" />
        <MacroBar label="Fat" actual={day.total_fat_g} target={nutrition.fat_g} unit="g" color="fat" />
      </div>

      {day.total_estimated_cost !== null && currency && (
        <p className="mt-3 text-sm text-zinc-400">
          Estimated cost: {currency} {Number(day.total_estimated_cost).toLocaleString()}
          {!day.cost_complete && " (partial — some foods lack pricing)"}
        </p>
      )}
    </div>
  );
}

const macroColors = {
  protein: { bar: "#FF4500", bg: "rgba(255,69,0,0.15)", text: "#FF6B3D" },
  carbs: { bar: "#00E5FF", bg: "rgba(0,229,255,0.12)", text: "#00E5FF" },
  fat: { bar: "#10B981", bg: "rgba(16,185,129,0.12)", text: "#34D399" },
} as const;

type MacroColor = keyof typeof macroColors;

function MacroBar({
  label,
  actual,
  target,
  unit,
  color,
}: {
  label: string;
  actual: number;
  target: number;
  unit: string;
  color: MacroColor;
}) {
  const pct = target > 0 ? Math.min(Math.round((actual / target) * 100), 100) : 0;
  const c = macroColors[color];

  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span style={{ color: c.text }}>{label}</span>
        <span className="font-medium" style={{ color: c.text }}>
          {Math.round(actual)}{unit}
        </span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full" style={{ background: c.bg }}>
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: c.bar }}
        />
      </div>
      <p className="mt-0.5 text-xs text-zinc-400">of {Math.round(target)}{unit}</p>
    </div>
  );
}

/* ── Helpers ──────────────────────────────────────────────────────────── */

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}
