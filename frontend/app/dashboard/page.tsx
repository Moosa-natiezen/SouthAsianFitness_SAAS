"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
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

function isProTier(u: AuthUser | null | undefined): boolean {
  if (!u) return false;
  return u.subscription_tier === "pro";
}

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
  const isPro = isProTier(user);

  return (
    <div className="space-y-6">
      {/* Upgrade celebration banner */}
      {showUpgradeBanner && !upgradeDismissed && (
        <div className="relative overflow-hidden rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-6 pr-10 neon-border">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-cyan-500/5" />
          <p className="relative text-sm font-medium text-emerald-300">
            🎉 Welcome to Pro! Your account has been upgraded. Enjoy unlimited meal plans!
          </p>
          <button
            type="button"
            onClick={() => setUpgradeDismissed(true)}
            className="absolute right-3 top-3 rounded p-1 text-emerald-400/60 hover:bg-emerald-500/10 hover:text-emerald-300"
            aria-label="Dismiss"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>
      )}

      {/* ── Cinematic Hero ─────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-2xl glass p-8">
        {/* Background glow */}
        <div className="absolute -left-20 -top-20 h-60 w-60 rounded-full bg-emerald-500/10 blur-[80px]" />
        <div className="absolute -bottom-20 -right-20 h-60 w-60 rounded-full bg-cyan-500/5 blur-[80px]" />
        <div className="absolute inset-0 bg-grid opacity-50" />

        <div className="relative">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
                Dashboard
              </p>
              <h1 className="mt-3 text-3xl font-bold tracking-tight text-white lg:text-4xl">
                {greeting}
              </h1>
              <p className="mt-2 max-w-lg text-sm text-zinc-400">
                Your personalized nutrition targets and today&apos;s meal plan.
              </p>
            </div>

            {/* Tier badge */}
            {user && (
              <div
                className={`flex items-center gap-2.5 self-start rounded-xl px-4 py-2.5 text-sm font-medium transition-all ${
                  isPro
                    ? "border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 shadow-[0_0_20px_rgba(16,185,129,0.15)]"
                    : "border border-white/[0.08] bg-white/[0.03] text-zinc-400"
                }`}
              >
                <span className={`h-2 w-2 rounded-full ${isPro ? "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)]" : "bg-zinc-500"}`} />
                {isPro ? "Pro" : "Free"}
              </div>
            )}
          </div>

          {/* Quick actions */}
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/dashboard/meal-plans"
              className="group flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2.5 text-sm font-medium text-emerald-300 transition-all hover:bg-emerald-500/20 hover:shadow-[0_0_20px_rgba(16,185,129,0.1)]"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
              </svg>
              AI Meal Generator ✨
            </Link>
            <Link
              href="/dashboard/food"
              className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-zinc-300 transition-all hover:bg-white/[0.06]"
            >
              <svg className="h-4 w-4 text-zinc-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
              </svg>
              Browse Foods
            </Link>
            <Link
              href="/dashboard/progress"
              className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-zinc-300 transition-all hover:bg-white/[0.06]"
            >
              <svg className="h-4 w-4 text-zinc-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
              </svg>
              Track Progress
            </Link>
          </div>
        </div>
      </div>

      {/* Loading */}
      {state.status === "loading" && (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-48 rounded-2xl" />
          <Skeleton className="h-48 rounded-2xl" />
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <AlertBanner variant="error" message={state.message} />
      )}

      {/* Content */}
      {state.status === "ready" && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <NutritionCard data={state.data} />
            <BudgetCard data={state.data} />
          </div>
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
    <div className="group relative overflow-hidden rounded-2xl glass p-6 transition-all duration-300 hover:shadow-[0_0_30px_rgba(16,185,129,0.05)]">
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-emerald-500/5 blur-[40px] transition-all duration-500 group-hover:bg-emerald-500/10" />
      <p className="relative text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
        Nutrition Targets
      </p>
      <h2 className="relative mt-3 text-xl font-semibold text-white">
        {goalLabel[n.goal] ?? n.goal} — {Math.round(n.calorie_target).toLocaleString()} kcal/day
      </h2>

      <div className="relative mt-4 grid grid-cols-3 gap-3">
        <MacroPill label="Protein" value={`${Math.round(n.protein_g)}g`} color="emerald" />
        <MacroPill label="Carbs" value={`${Math.round(n.carbs_g)}g`} color="cyan" />
        <MacroPill label="Fat" value={`${Math.round(n.fat_g)}g`} color="amber" />
      </div>

      <p className="relative mt-3 text-xs text-zinc-500">
        BMR {Math.round(n.bmr)} · TDEE {Math.round(n.tdee)}
      </p>

      {n.warnings.length > 0 && (
        <div className="relative mt-3 space-y-1">
          {n.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-400/80">⚠ {w}</p>
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
    <div className="group relative overflow-hidden rounded-2xl glass p-6 transition-all duration-300 hover:shadow-[0_0_30px_rgba(34,211,238,0.05)]">
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-cyan-500/5 blur-[40px] transition-all duration-500 group-hover:bg-cyan-500/10" />
      <p className="relative text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
        Budget
      </p>
      {hasBudget ? (
        <>
          <h2 className="relative mt-3 text-xl font-semibold text-white">
            {b.currency_code} {Number(b.daily_budget).toLocaleString()} / day
          </h2>
          <div className="relative mt-3 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl bg-white/[0.03] px-3 py-2">
              <p className="text-[11px] uppercase tracking-wider text-zinc-500">Weekly</p>
              <p className="font-semibold text-zinc-200">
                {b.currency_code} {Number(b.weekly_budget).toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl bg-white/[0.03] px-3 py-2">
              <p className="text-[11px] uppercase tracking-wider text-zinc-500">Monthly</p>
              <p className="font-semibold text-zinc-200">
                {b.currency_code} {Number(b.monthly_budget).toLocaleString()}
              </p>
            </div>
          </div>
        </>
      ) : (
        <p className="relative mt-3 text-sm text-zinc-400">
          No budget set. Add a weekly food budget in your profile to see budget targets.
        </p>
      )}

      {b.warnings.length > 0 && (
        <div className="relative mt-3 space-y-1">
          {b.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-400/80">⚠ {w}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function MacroPill({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "emerald" | "cyan" | "amber";
}) {
  const colors = {
    emerald: "from-emerald-500/10 to-emerald-500/5 border-emerald-500/20 text-emerald-300",
    cyan: "from-cyan-500/10 to-cyan-500/5 border-cyan-500/20 text-cyan-300",
    amber: "from-amber-500/10 to-amber-500/5 border-amber-500/20 text-amber-300",
  };

  return (
    <div className={`rounded-xl border bg-gradient-to-b px-3 py-3 text-center ${colors[color]}`}>
      <p className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</p>
      <p className="text-lg font-bold text-white">{value}</p>
    </div>
  );
}
