"use client";

import { useEffect, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Skeleton } from "@/components/ui/skeleton";
import { TodayPlanCard } from "@/components/dashboard/today-plan-card";
import {
  getNutritionAndBudget,
  type NutritionBudgetResponse,
} from "@/lib/api";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; data: NutritionBudgetResponse }
  | { status: "error"; message: string };

export default function DashboardPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    getNutritionAndBudget()
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Failed to load dashboard data.",
          });
        }
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
          Dashboard
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Welcome back</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Your personalized nutrition targets and today&apos;s meal plan.
        </p>
      </div>

      {state.status === "loading" && (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-48 rounded-2xl" />
          <Skeleton className="h-48 rounded-2xl" />
        </div>
      )}

      {state.status === "error" && (
        <AlertBanner variant="error" message={state.message} />
      )}

      {state.status === "ready" && (
        <>
          {/* Nutrition + Budget row */}
          <div className="grid gap-4 md:grid-cols-2">
            <NutritionCard data={state.data} />
            <BudgetCard data={state.data} />
          </div>

          {/* Today's plan */}
          <TodayPlanCard />
        </>
      )}
    </div>
  );
}

/* ── Sub-components ────────────────────────────────────────────────────── */

function NutritionCard({ data }: { data: NutritionBudgetResponse }) {
  const n = data.nutrition;
  const goalLabel: Record<string, string> = {
    weight_loss: "Weight Loss",
    weight_gain: "Weight Gain",
    muscle_building: "Muscle Building",
    general_fitness: "General Fitness",
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
        Nutrition Targets
      </p>
      <h2 className="mt-3 text-xl font-semibold text-slate-900">
        {goalLabel[n.goal] ?? n.goal} — {Math.round(n.calorie_target).toLocaleString()} kcal/day
      </h2>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <MacroPill label="Protein" value={`${Math.round(n.protein_g)}g`} />
        <MacroPill label="Carbs" value={`${Math.round(n.carbs_g)}g`} />
        <MacroPill label="Fat" value={`${Math.round(n.fat_g)}g`} />
      </div>

      <p className="mt-3 text-xs text-slate-500">
        BMR {Math.round(n.bmr)} · TDEE {Math.round(n.tdee)}
      </p>

      {n.warnings.length > 0 && (
        <div className="mt-3 space-y-1">
          {n.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-600">⚠ {w}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function BudgetCard({ data }: { data: NutritionBudgetResponse }) {
  const b = data.budget;
  const hasBudget = b.daily_budget !== null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
        Budget
      </p>
      {hasBudget ? (
        <>
          <h2 className="mt-3 text-xl font-semibold text-slate-900">
            {b.currency_code} {Number(b.daily_budget).toLocaleString()} / day
          </h2>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-slate-500">Weekly</p>
              <p className="font-medium text-slate-900">
                {b.currency_code} {Number(b.weekly_budget).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Monthly</p>
              <p className="font-medium text-slate-900">
                {b.currency_code} {Number(b.monthly_budget).toLocaleString()}
              </p>
            </div>
          </div>
        </>
      ) : (
        <p className="mt-3 text-slate-600">
          No budget set. Add a weekly food budget in your profile to see budget targets.
        </p>
      )}

      {b.warnings.length > 0 && (
        <div className="mt-3 space-y-1">
          {b.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-600">⚠ {w}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function MacroPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 px-3 py-2 text-center">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}
