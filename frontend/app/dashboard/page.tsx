"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AnimateIn, StaggerIn } from "@/components/animate-in";
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
    <div className="space-y-8">
      {/* ── Upgrade Banner ──────────────────────────────────────────── */}
      {showUpgradeBanner && !upgradeDismissed && (
        <AnimateIn delay={0} y={-10}>
          <div className="relative overflow-hidden rounded-2xl border border-[#c4854c]/20 bg-[#c4854c]/5 p-6 pr-10">
            <div className="absolute inset-0 bg-gradient-to-r from-[#c4854c]/10 to-[#e8a838]/5" />
            <p className="relative text-sm font-medium text-[#d4a574]">
              🎉 Welcome to Pro! Your account has been upgraded. Enjoy unlimited meal plans!
            </p>
            <button
              type="button"
              onClick={() => setUpgradeDismissed(true)}
              className="absolute right-3 top-3 rounded p-1 text-[#c4854c]/60 hover:bg-[#c4854c]/10 hover:text-[#d4a574]"
              aria-label="Dismiss"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
              </svg>
            </button>
          </div>
        </AnimateIn>
      )}

      {/* ── Hero — Editorial Typography ─────────────────────────────── */}
      <AnimateIn delay={0.1} y={40} blur={8}>
        <div className="relative overflow-hidden rounded-3xl border border-white/[0.04] bg-gradient-to-br from-[#141414] to-[#0a0a0a] p-8 md:p-12">
          {/* Decorative orbs */}
          <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-[#c4854c]/[0.06] blur-[100px]" />
          <div className="absolute -left-16 -bottom-16 h-48 w-48 rounded-full bg-[#e8a838]/[0.04] blur-[80px]" />
          <div className="absolute inset-0 bg-grid-editorial opacity-60" />

          <div className="relative">
            <p className="font-serif text-xs font-semibold uppercase tracking-[0.25em] text-[#c4854c]">
              Dashboard
            </p>
            <h1 className="mt-4 font-serif text-4xl font-bold tracking-tight text-[#f5f0e8] md:text-5xl lg:text-6xl">
              {greeting}
            </h1>
            <p className="mt-3 max-w-lg text-base text-[#8a8278]">
              Your personalized nutrition targets and today&apos;s meal plan.
            </p>

            {/* Quick actions */}
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/dashboard/meal-plans"
                className="btn-editorial group inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-[#c4854c] to-[#e8a838] px-5 py-3 text-sm font-semibold text-[#0a0a0a] shadow-lg shadow-[#c4854c]/20"
              >
                <span className="relative z-10 flex items-center gap-2">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                  AI Meal Generator
                </span>
              </Link>
              <Link
                href="/dashboard/food"
                className="inline-flex items-center gap-2 rounded-xl border border-white/[0.06] bg-white/[0.02] px-5 py-3 text-sm font-medium text-[#c8c0b4] transition-all hover:bg-white/[0.05] hover:text-[#f5f0e8]"
              >
                Browse Foods
              </Link>
              <Link
                href="/dashboard/progress"
                className="inline-flex items-center gap-2 rounded-xl border border-white/[0.06] bg-white/[0.02] px-5 py-3 text-sm font-medium text-[#c8c0b4] transition-all hover:bg-white/[0.05] hover:text-[#f5f0e8]"
              >
                Track Progress
              </Link>
            </div>
          </div>
        </div>
      </AnimateIn>

      {/* Loading */}
      {state.status === "loading" && (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-52 rounded-2xl bg-white/[0.03]" />
          <Skeleton className="h-52 rounded-2xl bg-white/[0.03]" />
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <div className="rounded-2xl border border-[#c25a3c]/20 bg-[#c25a3c]/10 p-4 text-sm text-[#c25a3c]">
          {state.message}
        </div>
      )}

      {/* ── Asymmetric Bento Grid ───────────────────────────────────── */}
      {state.status === "ready" && (
        <StaggerIn stagger={0.1} className="space-y-6">
          {/* Top row: nutrition (wide) + budget (narrow) */}
          <div className="grid gap-4 md:grid-cols-[1.4fr_0.6fr]">
            <NutritionCard data={state.data} />
            <BudgetCard data={state.data} />
          </div>

          {/* Today's plan — full width */}
          <TodayPlanCard />
        </StaggerIn>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   SUB-COMPONENTS — Editorial Glass Cards
   ═══════════════════════════════════════════════════════════════════════ */

function NutritionCard({ data }: { data: NutritionBudgetResponse }) {
  const n = data.nutrition;
  const goalLabel: Record<string, string> = {
    weight_loss: "Weight Loss",
    weight_gain: "Weight Gain",
    muscle_building: "Muscle Building",
    general_fitness: "General Fitness",
  };

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/[0.04] bg-gradient-to-br from-[#141414] to-[#0a0a0a] p-6 transition-all duration-500 hover:shadow-[0_0_40px_rgba(196,133,76,0.04)]">
      <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full bg-[#c4854c]/[0.05] blur-[50px] transition-all duration-700 group-hover:bg-[#c4854c]/[0.08]" />

      <p className="relative font-serif text-[11px] font-semibold uppercase tracking-[0.25em] text-[#c4854c]">
        Nutrition Targets
      </p>
      <h2 className="relative mt-3 font-serif text-xl font-semibold text-[#f5f0e8]">
        {goalLabel[n.goal] ?? n.goal}
      </h2>
      <p className="relative mt-1 text-2xl font-bold text-gradient-cardamom">
        {Math.round(n.calorie_target).toLocaleString()} <span className="text-sm font-normal text-[#8a8278]">kcal/day</span>
      </p>

      <div className="relative mt-5 grid grid-cols-3 gap-3">
        <MacroPill label="Protein" value={`${Math.round(n.protein_g)}g`} color="cardamom" />
        <MacroPill label="Carbs" value={`${Math.round(n.carbs_g)}g`} color="saffron" />
        <MacroPill label="Fat" value={`${Math.round(n.fat_g)}g`} color="terracotta" />
      </div>

      <p className="relative mt-4 text-[11px] text-[#8a8278]">
        BMR {Math.round(n.bmr)} · TDEE {Math.round(n.tdee)}
      </p>

      {n.warnings.length > 0 && (
        <div className="relative mt-3 space-y-1">
          {n.warnings.map((w, i) => (
            <p key={i} className="text-[11px] text-[#e8a838]/70">⚠ {w}</p>
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
    <div className="group relative overflow-hidden rounded-2xl border border-white/[0.04] bg-gradient-to-br from-[#141414] to-[#0a0a0a] p-6 transition-all duration-500 hover:shadow-[0_0_40px_rgba(232,168,56,0.04)]">
      <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full bg-[#e8a838]/[0.04] blur-[50px] transition-all duration-700 group-hover:bg-[#e8a838]/[0.08]" />

      <p className="relative font-serif text-[11px] font-semibold uppercase tracking-[0.25em] text-[#e8a838]">
        Budget
      </p>
      {hasBudget ? (
        <>
          <h2 className="relative mt-3 font-serif text-xl font-semibold text-[#f5f0e8]">
            {b.currency_code} {Number(b.daily_budget).toLocaleString()} <span className="text-sm font-normal text-[#8a8278]">/ day</span>
          </h2>
          <div className="relative mt-4 space-y-2">
            <div className="flex items-center justify-between rounded-xl bg-white/[0.02] px-3 py-2.5">
              <span className="text-[10px] uppercase tracking-wider text-[#8a8278]">Weekly</span>
              <span className="text-sm font-semibold text-[#c8c0b4]">
                {b.currency_code} {Number(b.weekly_budget).toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl bg-white/[0.02] px-3 py-2.5">
              <span className="text-[10px] uppercase tracking-wider text-[#8a8278]">Monthly</span>
              <span className="text-sm font-semibold text-[#c8c0b4]">
                {b.currency_code} {Number(b.monthly_budget).toLocaleString()}
              </span>
            </div>
          </div>
        </>
      ) : (
        <p className="relative mt-3 text-sm text-[#8a8278]">
          No budget set. Add a weekly food budget in your profile to see budget targets.
        </p>
      )}

      {b.warnings.length > 0 && (
        <div className="relative mt-3 space-y-1">
          {b.warnings.map((w, i) => (
            <p key={i} className="text-[11px] text-[#e8a838]/70">⚠ {w}</p>
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
  color: "cardamom" | "saffron" | "terracotta";
}) {
  const colors = {
    cardamom: "border-[#c4854c]/20 bg-[#c4854c]/[0.06] text-[#d4a574]",
    saffron: "border-[#e8a838]/20 bg-[#e8a838]/[0.06] text-[#f0c060]",
    terracotta: "border-[#c25a3c]/20 bg-[#c25a3c]/[0.06] text-[#d4715a]",
  };

  return (
    <div className={`rounded-xl border px-3 py-3 text-center ${colors[color]}`}>
      <p className="text-[9px] uppercase tracking-wider text-[#8a8278]">{label}</p>
      <p className="text-lg font-bold text-[#f5f0e8]">{value}</p>
    </div>
  );
}
