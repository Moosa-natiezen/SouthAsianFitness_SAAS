"use client";

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

/** Check all possible tier key variants for robustness. */
function isProTier(u: AuthUser | null | undefined): boolean {
  if (!u) return false;
  return (
    u.subscription_tier === "pro" ||
    (u as Record<string, unknown>).tier === "pro" ||
    (u as Record<string, unknown>).is_pro === true
  );
}

export default function DashboardPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [displayName, setDisplayName] = useState<string | null>(null);

  /* ── Upgrade banner ────────────────────────────────────────────────
   * Capture the flag from the raw URL *once* on mount, then immediately
   * clean the URL so a refresh never re-shows the banner.
   * The banner persists in React state independent of the URL.
   */
  const [showUpgradeBanner, setShowUpgradeBanner] = useState(false);
  const [upgradeDismissed, setUpgradeDismissed] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("upgraded") === "true") {
      setShowUpgradeBanner(true);
      // Clean the URL bar without triggering a navigation/re-render
      window.history.replaceState({}, "", "/dashboard");
    }
  }, []);

  /* ── Initial data load ────────────────────────────────────────────── */

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((user) => {
        setUserState(user);
        if (!cancelled && user.display_name) {
          setDisplayName(user.display_name);
        }
      })
      .catch(() => {
        // Non-critical: dashboard still works without the name
      });
    return () => { cancelled = true; };
  }, []);

  /* ── Initial data load ────────────────────────────────────────────── */

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((user) => {
        setUserState(user);
        if (!cancelled && user.display_name) {
          setDisplayName(user.display_name);
        }
      })
      .catch(() => {
        // Non-critical: dashboard still works without the name
      });
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

  const greeting = displayName ? `Welcome back, ${displayName}` : "Welcome back";

  return (
    <div className="space-y-6">
      {/* Upgrade celebration banner */}
      {showUpgradeBanner && !upgradeDismissed && (
        <div className="relative rounded-2xl border border-emerald-200 bg-emerald-50 p-6 pr-10 shadow-sm">
          <p className="text-sm font-medium text-emerald-800">
            🎉 Welcome to Pro! Your account has been upgraded. Enjoy unlimited meal plans!
          </p>
          <button
            type="button"
            onClick={() => setUpgradeDismissed(true)}
            className="absolute right-3 top-3 rounded p-1 text-emerald-600 hover:bg-emerald-100 hover:text-emerald-800"
            aria-label="Dismiss"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>
      )}

      {/* Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
          Dashboard
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">{greeting}</h1>
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
