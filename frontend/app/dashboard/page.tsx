"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { TodayPlanCard } from "@/components/dashboard/today-plan-card";
import {
  getCurrentUser,
  getNutritionAndBudget,
  type AuthUser,
  type NutritionBudgetResponse,
} from "@/lib/api";
import { setUserState } from "@/lib/user-state";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; data: NutritionBudgetResponse }
  | { status: "error"; message: string };

export default function DashboardPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [user, setUser] = useState<AuthUser | null>(null);
  const [showUpgradeBanner, setShowUpgradeBanner] = useState(false);
  const [upgradeDismissed, setUpgradeDismissed] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("upgraded") === "true") {
      setShowUpgradeBanner(true);
      window.history.replaceState({}, "", "/dashboard");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((u) => {
        setUserState(u);
        if (!cancelled) setUser(u);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

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

  const greeting = user?.display_name
    ? `Welcome back, ${user.display_name}`
    : "Welcome back";

  return (
    <div className="space-y-6">
      {/* Upgrade banner */}
      {showUpgradeBanner && !upgradeDismissed && (
        <div className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.04] px-4 py-3 text-sm">
          <span className="text-zinc-300">🎉 Welcome to Pro! Your account has been upgraded.</span>
          <button
            type="button"
            onClick={() => setUpgradeDismissed(true)}
            className="ml-4 text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Hero */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{greeting}</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Your personalized nutrition targets and today&apos;s meal plan.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href="/dashboard/meal-plans"
            className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-[#09090b] hover:bg-zinc-200 transition-colors"
          >
            AI Meal Generator
          </Link>
          <Link
            href="/dashboard/food"
            className="rounded-lg border border-white/10 px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white hover:border-white/20 transition-colors"
          >
            Browse Foods
          </Link>
          <Link
            href="/dashboard/progress"
            className="rounded-lg border border-white/10 px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white hover:border-white/20 transition-colors"
          >
            Track Progress
          </Link>
        </div>
      </div>

      {/* Loading */}
      {state.status === "loading" && (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-40 rounded-lg bg-white/[0.04]" />
          <Skeleton className="h-40 rounded-lg bg-white/[0.04]" />
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <div className="rounded-lg border border-white/8 bg-[#18181b] p-4 text-sm text-zinc-400">
          {state.message}
        </div>
      )}

      {/* Stats */}
      {state.status === "ready" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <NutritionCard data={state.data} />
            <BudgetCard data={state.data} />
          </div>
          <TodayPlanCard />
        </div>
      )}
    </div>
  );
}

/* ── Nutrition Card ─────────────────────────────────────────────────── */

function NutritionCard({ data }: { data: NutritionBudgetResponse }) {
  const n = data.nutrition;
  const goalLabel: Record<string, string> = {
    weight_loss: "Weight Loss",
    weight_gain: "Weight Gain",
    muscle_building: "Muscle Building",
    general_fitness: "General Fitness",
  };

  return (
    <div className="rounded-lg border border-white/8 bg-[#18181b] p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Nutrition Targets
      </p>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-bold tabular-nums">
          {Math.round(n.calorie_target).toLocaleString()}
        </span>
        <span className="text-sm text-zinc-500">kcal / day</span>
      </div>
      <p className="mt-1 text-sm text-zinc-400">{goalLabel[n.goal] ?? n.goal}</p>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <StatBlock label="Protein" value={`${Math.round(n.protein_g)}g`} />
        <StatBlock label="Carbs" value={`${Math.round(n.carbs_g)}g`} />
        <StatBlock label="Fat" value={`${Math.round(n.fat_g)}g`} />
      </div>

      <p className="mt-3 text-xs text-zinc-600">
        BMR {Math.round(n.bmr)} · TDEE {Math.round(n.tdee)}
      </p>
    </div>
  );
}

/* ── Budget Card ────────────────────────────────────────────────────── */

function BudgetCard({ data }: { data: NutritionBudgetResponse }) {
  const b = data.budget;
  const hasBudget = b.daily_budget !== null;

  return (
    <div className="rounded-lg border border-white/8 bg-[#18181b] p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Budget
      </p>
      {hasBudget ? (
        <>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tabular-nums">
              {Number(b.daily_budget).toLocaleString()}
            </span>
            <span className="text-sm text-zinc-500">{b.currency_code} / day</span>
          </div>
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-500">Weekly</span>
              <span className="font-medium text-zinc-300 tabular-nums">
                {b.currency_code} {Number(b.weekly_budget).toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-500">Monthly</span>
              <span className="font-medium text-zinc-300 tabular-nums">
                {b.currency_code} {Number(b.monthly_budget).toLocaleString()}
              </span>
            </div>
          </div>
        </>
      ) : (
        <p className="mt-3 text-sm text-zinc-500">
          No budget set. Add one in your profile settings.
        </p>
      )}
    </div>
  );
}

/* ── Stat Block ─────────────────────────────────────────────────────── */

function StatBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/[0.03] px-3 py-2.5">
      <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">{label}</p>
      <p className="mt-0.5 text-lg font-bold tabular-nums">{value}</p>
    </div>
  );
}
