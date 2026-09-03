"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Skeleton } from "@/components/ui/skeleton";
import {
  deleteSavedAiMealPlan,
  listSavedAiMealPlans,
  type SavedMealPlanItem,
  type SavedMealPlanListResponse,
} from "@/lib/api";

export default function SavedPlansPage() {
  const [state, setState] = useState<
    | { status: "loading" }
    | { status: "ready"; data: SavedMealPlanListResponse }
    | { status: "error"; message: string }
  >({ status: "loading" });

  const [selectedPlan, setSelectedPlan] = useState<SavedMealPlanItem | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleteMsg, setDeleteMsg] = useState<{ type: "info" | "error"; text: string } | null>(null);

  const fetchPlans = () => {
    setState({ status: "loading" });
    listSavedAiMealPlans({ limit: 50 })
      .then((data) => setState({ status: "ready", data }))
      .catch((err: unknown) =>
        setState({
          status: "error",
          message: err instanceof Error ? err.message : "Failed to load saved plans.",
        }),
      );
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleDelete = async (planId: string) => {
    setDeleteId(planId);
    setDeleteMsg(null);
    try {
      await deleteSavedAiMealPlan(planId);
      setDeleteMsg({ type: "info", text: "Plan deleted." });
      fetchPlans();
    } catch (err: unknown) {
      setDeleteMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to delete plan.",
      });
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl glass p-6">
        <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/50/5 blur-[40px]" />
        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-600">
            AI Meal Plans
          </p>
          <h1 className="mt-2 text-2xl font-bold text-stone-900">Saved Plans</h1>
          <p className="mt-1 text-sm text-stone-500">
            Your archived AI-generated meal plans. Click any plan to read the full details.
          </p>
        </div>
      </div>

      {/* Notifications */}
      {deleteMsg && (
        <AlertBanner variant={deleteMsg.type} message={deleteMsg.text} />
      )}

      {/* Loading */}
      {state.status === "loading" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-48 rounded-2xl bg-stone-50" />
          ))}
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <AlertBanner variant="error" message={state.message} />
      )}

      {/* Empty state */}
      {state.status === "ready" && state.data.items.length === 0 && (
        <div className="rounded-2xl border border-dashed border-stone-200 bg-white/2 p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10">
            <svg className="h-7 w-7 text-stone-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
            </svg>
          </div>
          <h2 className="mt-4 text-lg font-semibold text-stone-900">No saved plans yet</h2>
          <p className="mt-2 text-sm text-stone-500">
            Generate an AI meal plan and click &quot;Save to My Plans&quot; to see it here.
          </p>
        </div>
      )}

      {/* Bento grid */}
      {state.status === "ready" && state.data.items.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {state.data.items.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              onSelect={setSelectedPlan}
              onDelete={handleDelete}
              deleting={deleteId === plan.id}
            />
          ))}
        </div>
      )}

      {/* Modal viewer */}
      {selectedPlan && (
        <PlanModal plan={selectedPlan} onClose={() => setSelectedPlan(null)} />
      )}
    </div>
  );
}

/* ── Plan Card ─────────────────────────────────────────────────────── */

function PlanCard({
  plan,
  onSelect,
  onDelete,
  deleting,
}: {
  plan: SavedMealPlanItem;
  onSelect: (plan: SavedMealPlanItem) => void;
  onDelete: (id: string) => void;
  deleting: boolean;
}) {
  const createdDate = formatDate(plan.created_at);

  return (
    <div className="group relative overflow-hidden rounded-2xl glass p-5 transition-all duration-300 hover:shadow-[0_0_30px_rgba(16,185,129,0.05)]">
      <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-white/50/5 blur-[30px] transition-all duration-500 group-hover:bg-stone-100" />

      <div className="relative">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold text-stone-900 line-clamp-1">{plan.title}</h3>
          <span className="shrink-0 rounded-md bg-white/10 px-1.5 py-0.5 text-[10px] font-semibold text-stone-600">
            AI
          </span>
        </div>

        {/* Meta pills */}
        <div className="mt-2 flex flex-wrap gap-1.5">
          {plan.target_calories && (
            <span className="rounded-md bg-stone-50 px-2 py-0.5 text-[10px] text-stone-500">
              {plan.target_calories} kcal
            </span>
          )}
          {plan.protein_g && (
            <span className="rounded-md bg-stone-50 px-2 py-0.5 text-[10px] text-stone-500">
              {plan.protein_g}g protein
            </span>
          )}
        </div>

        {/* Content preview */}
        <div className="mt-3 line-clamp-4 text-xs leading-relaxed text-stone-500">
          {plan.content.slice(0, 200)}...
        </div>

        {/* Footer */}
        <div className="mt-4 flex items-center justify-between border-t border-stone-200 pt-3">
          <span className="text-[10px] text-stone-500">{createdDate}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onSelect(plan)}
              className="rounded-lg bg-white/10 px-3 py-1.5 text-[11px] font-medium text-stone-600 transition-all hover:bg-white/50/20"
            >
              View
            </button>
            <button
              onClick={() => onDelete(plan.id)}
              disabled={deleting}
              className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-1.5 text-[11px] font-medium text-stone-500 transition-all hover:bg-red-500/10 hover:text-red-300 disabled:opacity-50"
            >
              {deleting ? "..." : "Delete"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Plan Modal ────────────────────────────────────────────────────── */

function PlanModal({
  plan,
  onClose,
}: {
  plan: SavedMealPlanItem;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        className="relative max-h-[85vh] w-full max-w-3xl overflow-hidden rounded-2xl glass-strong"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-stone-200 bg-[#0a0a0a]/90 px-6 py-4 backdrop-blur-xl">
          <div>
            <h2 className="text-lg font-semibold text-stone-900">{plan.title}</h2>
            <div className="mt-1 flex items-center gap-3 text-xs text-stone-500">
              <span>{formatDate(plan.created_at)}</span>
              {plan.target_calories && <span>· {plan.target_calories} kcal</span>}
              {plan.protein_g && <span>· {plan.protein_g}g protein</span>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-stone-500 transition-colors hover:bg-stone-50 hover:text-stone-600"
            aria-label="Close"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto px-6 py-6" style={{ maxHeight: "calc(85vh - 80px)" }}>
          <div className="prose prose-sm prose-invert prose-zinc max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {plan.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Helpers ──────────────────────────────────────────────────────────── */

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}
