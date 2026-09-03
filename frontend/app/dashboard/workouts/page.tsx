"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AiWorkoutGenerator } from "@/components/ai/ai-workout-generator";
import {
  deleteSavedAiWorkout,
  listSavedAiWorkouts,
  type SavedWorkoutPlanItem,
  type SavedWorkoutPlanListResponse,
} from "@/lib/api";

type Tab = "generator" | "archive";

const goalLabels: Record<string, string> = {
  strength: "Strength",
  hypertrophy: "Hypertrophy",
  endurance: "Endurance",
  fat_loss: "Fat Loss",
};

const splitLabels: Record<string, string> = {
  push_pull_legs: "PPL",
  upper_lower: "Upper/Lower",
  full_body: "Full Body",
};

export default function WorkoutsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("generator");
  const [archive, setArchive] = useState<SavedWorkoutPlanListResponse | null>(null);
  const [archiveLoading, setArchiveLoading] = useState(true);
  const [archiveError, setArchiveError] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [viewing, setViewing] = useState<SavedWorkoutPlanItem | null>(null);

  const fetchArchive = () => {
    setArchiveLoading(true);
    listSavedAiWorkouts({ limit: 20 })
      .then(setArchive)
      .catch((err: unknown) => {
        setArchiveError(err instanceof Error ? err.message : "Failed to load archive.");
      })
      .finally(() => setArchiveLoading(false));
  };

  useEffect(() => {
    fetchArchive();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDelete = async (id: string) => {
    setDeleteId(id);
    try {
      await deleteSavedAiWorkout(id);
      fetchArchive();
    } catch {
      // silently fail
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header + tabs */}
      <div className="rounded-2xl border border-stone-200 bg-white p-6 backdrop-blur-xl">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
          Workout Studio
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-stone-900">
          AI Workout Generator
        </h1>
        <p className="mt-2 text-stone-500">
          Generate progressive overload routines with AI, or browse your saved programs.
        </p>

        <div className="mt-6 flex gap-2">
          <button
            onClick={() => setActiveTab("generator")}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
              activeTab === "generator"
                ? "border-stone-300 bg-white/8 text-stone-900"
                : "border-stone-200 bg-stone-50 text-stone-500 hover:bg-stone-50"
            }`}
          >
            Generator
          </button>
          <button
            onClick={() => setActiveTab("archive")}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
              activeTab === "archive"
                ? "border-stone-300 bg-white/8 text-stone-900"
                : "border-stone-200 bg-stone-50 text-stone-500 hover:bg-stone-50"
            }`}
          >
            Archive {archive && archive.total > 0 && (
              <span className="ml-1.5 rounded-full bg-white/10 px-1.5 py-0.5 text-[10px]">
                {archive.total}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Generator tab */}
      {activeTab === "generator" && <AiWorkoutGenerator />}

      {/* Archive tab */}
      {activeTab === "archive" && (
        <div className="rounded-2xl border border-stone-200 bg-white p-6 backdrop-blur-xl">
          <h2 className="text-lg font-semibold text-stone-900">Saved Workouts</h2>
          <p className="mt-1 text-sm text-stone-500">
            Your archived AI-generated workout programs.
          </p>

          {archiveLoading && (
            <div className="mt-4 space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          )}

          {archiveError && (
            <AlertBanner variant="error" message={archiveError} className="mt-4" />
          )}

          {!archiveLoading && archive && archive.items.length === 0 && (
            <p className="mt-4 text-sm text-stone-500">
              No saved workouts yet. Generate one in the Generator tab!
            </p>
          )}

          {!archiveLoading && archive && archive.items.length > 0 && (
            <div className="mt-4 space-y-3">
              {archive.items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-xl border border-stone-200 bg-stone-50 p-4 transition hover:bg-stone-50"
                >
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate text-sm font-semibold text-stone-900">
                      {item.title}
                    </h3>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs text-stone-500">
                      {item.goal && (
                        <span className="rounded bg-stone-50 px-1.5 py-0.5">
                          {goalLabels[item.goal] ?? item.goal}
                        </span>
                      )}
                      {item.split && (
                        <span className="rounded bg-stone-50 px-1.5 py-0.5">
                          {splitLabels[item.split] ?? item.split}
                        </span>
                      )}
                      {item.equipment && (
                        <span className="rounded bg-stone-50 px-1.5 py-0.5 capitalize">
                          {item.equipment}
                        </span>
                      )}
                      <span>
                        {new Date(item.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-stone-200 bg-stone-50"
                      onClick={() => setViewing(item)}
                    >
                      View
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(item.id)}
                      disabled={deleteId === item.id}
                    >
                      {deleteId === item.id ? "..." : "Delete"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Workout Viewer Modal */}
      {viewing && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          onClick={() => setViewing(null)}
        >
          <div
            className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-stone-200 bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-stone-900">{viewing.title}</h2>
              <button
                onClick={() => setViewing(null)}
                className="rounded-lg p-1 text-stone-500 transition hover:bg-stone-50 hover:text-stone-900"
              >
                ✕
              </button>
            </div>
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {viewing.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
