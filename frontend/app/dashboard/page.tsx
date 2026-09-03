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

  const isPro = user?.subscription_tier === "pro";

  return (
    <div className="space-y-6">
      {/* Upgrade banner */}
      {showUpgradeBanner && !upgradeDismissed && (
        <div className="glass rounded-xl px-5 py-4 text-sm animate-fade-in-up">
          <div className="flex items-center justify-between">
            <span className="text-emerald-600">
              <span className="mr-2">🎉</span>Welcome to Pro! Your account has been upgraded.
            </span>
            <button
              type="button"
              onClick={() => setUpgradeDismissed(true)}
              className="ml-4 text-stone-400 dark:text-zinc-500 hover:text-stone-600 dark:text-zinc-400 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Hero */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-stone-900 dark:text-zinc-100">{greeting}</h1>
            <p className="mt-1 text-sm text-stone-500 dark:text-zinc-500">
              Your personalized nutrition targets and today&apos;s meal plan.
            </p>
          </div>
          {user && (
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold transition-all duration-300 ${
                isPro
                  ? "bg-gradient-to-r from-emerald-700 to-emerald-600 text-stone-900 dark:text-zinc-100 shadow-lg shadow-emerald-700/25 animate-glow-ring"
                  : "bg-stone-100 dark:bg-zinc-800 text-stone-500 dark:text-zinc-500 border border-stone-200 dark:border-zinc-700"
              }`}
            >
              {isPro ? "✦ Pro" : "Free"}
            </span>
          )}
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            href="/dashboard/meal-plans"
            className="btn-chrome-accent rounded-xl px-5 py-2.5 text-sm font-semibold"
          >
            AI Meal Generator
          </Link>
          <Link
            href="/dashboard/food"
            className="btn-chrome rounded-xl px-5 py-2.5 text-sm font-medium text-stone-600 dark:text-zinc-400"
          >
            Browse Foods
          </Link>
          <Link
            href="/dashboard/progress"
            className="btn-chrome rounded-xl px-5 py-2.5 text-sm font-medium text-stone-600 dark:text-zinc-400"
          >
            Track Progress
          </Link>
        </div>
      </div>

      {/* Loading */}
      {state.status === "loading" && (
        <div className="grid gap-5 md:grid-cols-2">
          <Skeleton className="h-48 rounded-2xl bg-stone-100 dark:bg-zinc-800" />
          <Skeleton className="h-48 rounded-2xl bg-stone-100 dark:bg-zinc-800" />
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <div className="glass rounded-2xl p-5 text-sm text-stone-500 dark:text-zinc-500">
          {state.message}
        </div>
      )}

      {/* Stats */}
      {state.status === "ready" && (
        <div className="space-y-5">
          <div className="grid gap-5 md:grid-cols-2">
            <NutritionCard data={state.data} />
            <BudgetCard data={state.data} />
          </div>
          <TodayPlanCard />
          <AchievementsSection />
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

  const totalMacro = n.protein_g + n.carbs_g + n.fat_g;
  const proteinPct = totalMacro > 0 ? (n.protein_g / totalMacro) * 100 : 0;
  const carbsPct = totalMacro > 0 ? (n.carbs_g / totalMacro) * 100 : 0;
  const fatPct = totalMacro > 0 ? (n.fat_g / totalMacro) * 100 : 0;

  return (
    <div className="glass rounded-2xl p-6 card-hover">
      <p className="text-xs font-medium uppercase tracking-[0.15em] text-emerald-600">
        Nutrition Targets
      </p>
      <div className="mt-4 flex items-end gap-3">
        <span className="text-3xl font-bold text-stone-900 dark:text-zinc-100 tabular-nums">
          {Math.round(n.calorie_target).toLocaleString()}
        </span>
        <span className="text-sm text-stone-400 dark:text-zinc-500 mb-1">kcal / day</span>
      </div>
      <p className="mt-1 text-sm text-stone-500 dark:text-zinc-500">{goalLabel[n.goal] ?? n.goal}</p>

      {/* Macro progress bars */}
      <div className="mt-5 space-y-3">
        <MacroBar label="Protein" value={Math.round(n.protein_g)} unit="g" pct={proteinPct} color="var(--macro-protein)" />
        <MacroBar label="Carbs" value={Math.round(n.carbs_g)} unit="g" pct={carbsPct} color="var(--macro-carbs)" />
        <MacroBar label="Fat" value={Math.round(n.fat_g)} unit="g" pct={fatPct} color="var(--macro-fat)" />
      </div>

      <p className="mt-4 text-xs text-stone-400 dark:text-zinc-500">
        BMR {Math.round(n.bmr)} · TDEE {Math.round(n.tdee)}
      </p>
    </div>
  );
}

/* ── Macro Bar ──────────────────────────────────────────────────────── */

function MacroBar({ label, value, unit, pct, color }: {
  label: string;
  value: number;
  unit: string;
  pct: number;
  color: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1.5">
        <span className="text-stone-500 dark:text-zinc-500">{label}</span>
        <span className="text-stone-600 dark:text-zinc-400 tabular-nums font-medium">{value}{unit}</span>
      </div>
      <div className="h-1.5 rounded-full bg-stone-100 dark:bg-zinc-800 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

/* ── Budget Card ────────────────────────────────────────────────────── */

function BudgetCard({ data }: { data: NutritionBudgetResponse }) {
  const b = data.budget;
  const hasBudget = b.daily_budget !== null;

  return (
    <div className="glass rounded-2xl p-6 card-hover">
      <p className="text-xs font-medium uppercase tracking-[0.15em] text-emerald-600">
        Budget
      </p>
      {hasBudget ? (
        <>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-stone-900 dark:text-zinc-100 tabular-nums">
              {Number(b.daily_budget).toLocaleString()}
            </span>
            <span className="text-sm text-stone-400 dark:text-zinc-500">{b.currency_code} / day</span>
          </div>
          <div className="mt-5 space-y-3">
            <div className="flex items-center justify-between text-sm glass rounded-lg px-4 py-2.5">
              <span className="text-stone-400 dark:text-zinc-500">Weekly</span>
              <span className="font-medium text-stone-700 dark:text-zinc-300 tabular-nums">
                {b.currency_code} {Number(b.weekly_budget).toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm glass rounded-lg px-4 py-2.5">
              <span className="text-stone-400 dark:text-zinc-500">Monthly</span>
              <span className="font-medium text-stone-700 dark:text-zinc-300 tabular-nums">
                {b.currency_code} {Number(b.monthly_budget).toLocaleString()}
              </span>
            </div>
          </div>
        </>
      ) : (
        <p className="mt-4 text-sm text-stone-400 dark:text-zinc-500">
          No budget set. Add one in your profile settings.
        </p>
      )}
    </div>
  );
}

/* ── Achievements Section ───────────────────────────────────────────── */

function AchievementsSection() {
  const badges = [
    { icon: "🔥", label: "7-Day Streak", desc: "Logged in for 7 days straight", glow: "from-emerald-600/20 to-amber-500/10" },
    { icon: "📊", label: "First Entry", desc: "Logged your first progress entry", glow: "from-emerald-700/20 to-emerald-600/10" },
    { icon: "🎯", label: "Goal Setter", desc: "Set your nutrition targets", glow: "from-emerald-500/20 to-teal-500/10" },
  ];

  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-[0.15em] text-stone-400 dark:text-zinc-500 mb-4">
        Your Progress Badges
      </p>
      <div className="grid grid-cols-3 gap-4">
        {badges.map((badge) => (
          <div
            key={badge.label}
            className="glass rounded-2xl p-5 text-center card-hover group cursor-default"
          >
            <div className={`mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${badge.glow} text-2xl transition-transform duration-300 group-hover:scale-110`}>
              {badge.icon}
            </div>
            <p className="mt-3 text-sm font-medium text-stone-900 dark:text-zinc-100">{badge.label}</p>
            <p className="mt-1 text-xs text-stone-400 dark:text-zinc-500 leading-relaxed">{badge.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
