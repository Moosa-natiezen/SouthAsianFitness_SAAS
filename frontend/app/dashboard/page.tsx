"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";

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

/**
 * Maximum number of polling attempts to wait for the webhook to
 * process the upgrade before giving up.
 */
const MAX_POLL_ATTEMPTS = 15;
const POLL_INTERVAL_MS = 2000;

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
  const searchParams = useSearchParams();
  const router = useRouter();

  /* ── Upgrade polling ─────────────────────────────────────────────── */
  const [upgradeBanner, setUpgradeBanner] = useState<
    { kind: "processing" } | { kind: "success" } | null
  >(() => (searchParams.get("upgraded") === "true" ? { kind: "processing" } : null));

  /**
   * Clear the ?upgraded=true query param from the URL without
   * triggering a navigation/re-render.
   */
  const cleanUpgradedParam = useCallback(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.has("upgraded")) {
      url.searchParams.delete("upgraded");
      window.history.replaceState({}, "", url.toString());
    }
  }, []);

  /* Poll getCurrentUser() until subscription_tier flips to "pro" */
  useEffect(() => {
    if (searchParams.get("upgraded") !== "true") return;

    let cancelled = false;
    let attempt = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const poll = async () => {
      while (!cancelled && attempt < MAX_POLL_ATTEMPTS) {
        attempt++;
        try {
          const user: AuthUser = await getCurrentUser();
          if (cancelled) return;

          setUserState(user);
          if (isProTier(user)) {
            setUpgradeBanner({ kind: "success" });
            cleanUpgradedParam();
            return;
          }
        } catch {
          // Transient network error — keep polling
        }
        // Wait before next attempt
        await new Promise<void>((resolve) => {
          timer = setTimeout(resolve, POLL_INTERVAL_MS);
        });
      }
      // Timed out — still show a soft message so the user knows to refresh
      if (!cancelled) {
        setUpgradeBanner(null);
        cleanUpgradedParam();
      }
    };

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [searchParams, cleanUpgradedParam]);

  /* Re-fetch user on visibility change (handles tab-switch after checkout) */
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === "visible" && upgradeBanner?.kind === "processing") {
        void getCurrentUser().then((user) => {
          setUserState(user);
          if (isProTier(user)) {
            setUpgradeBanner({ kind: "success" });
            cleanUpgradedParam();
          }
        }).catch(() => {});
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [upgradeBanner?.kind, cleanUpgradedParam]);

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
      {/* Upgrade banners */}
      {upgradeBanner?.kind === "processing" && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm" role="status">
          <p className="text-center text-sm font-medium text-emerald-800">
            ⏳ Processing your upgrade… We&apos;ll update your plan once the payment is confirmed.
          </p>
        </div>
      )}
      {upgradeBanner?.kind === "success" && (
        <AlertBanner
          variant="info"
          message="🎉 Welcome to Pro! Your subscription is now active. Enjoy unlimited meal plans!"
        />
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
