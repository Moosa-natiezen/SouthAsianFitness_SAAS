"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Button } from "@/components/ui/button";
import { saveAiWorkout, type SaveWorkoutPlanPayload } from "@/lib/api";
import { useWorkoutStream } from "@/hooks/use-workout-stream";

/* ── Constants ─────────────────────────────────────────────────────────── */

const goals = [
  { value: "strength", label: "Strength", icon: "🏋️", desc: "Max force production" },
  { value: "hypertrophy", label: "Hypertrophy", icon: "💪", desc: "Muscle growth" },
  { value: "endurance", label: "Endurance", icon: "🏃", desc: "Muscular stamina" },
  { value: "fat_loss", label: "Fat Loss", icon: "🔥", desc: "Cut & conditioning" },
] as const;

const experienceLevels = [
  { value: "beginner", label: "Beginner", desc: "< 1 year" },
  { value: "intermediate", label: "Intermediate", desc: "1–3 years" },
  { value: "advanced", label: "Advanced", desc: "3+ years" },
] as const;

const splits = [
  { value: "push_pull_legs", label: "Push / Pull / Legs" },
  { value: "upper_lower", label: "Upper / Lower" },
  { value: "full_body", label: "Full Body" },
] as const;

const equipmentOptions = [
  { value: "gym", label: "Full Gym", icon: "🏗️" },
  { value: "dumbbells", label: "Dumbbells", icon: "🏋️" },
  { value: "bodyweight", label: "Bodyweight", icon: "🤸" },
] as const;

/* ── Component ─────────────────────────────────────────────────────────── */

export function AiWorkoutGenerator() {
  const { content, isStreaming, error, isSandbox, generate, abort, reset } =
    useWorkoutStream();

  const [goal, setGoal] = useState<string>("hypertrophy");
  const [experience, setExperience] = useState<string>("intermediate");
  const [split, setSplit] = useState<string>("push_pull_legs");
  const [equipment, setEquipment] = useState<string>("gym");

  // Save state
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const handleGenerate = () => {
    setSaveMsg(null);
    generate({ goal, experience_level: experience, split, equipment });
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setSaveMsg("Copied to clipboard!");
      setTimeout(() => setSaveMsg(null), 2000);
    } catch {
      setSaveMsg("Failed to copy");
    }
  };

  const handleSave = async () => {
    if (!content.trim()) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      const goalLabel = goals.find((g) => g.value === goal)?.label ?? goal;
      const payload: SaveWorkoutPlanPayload = {
        title: `${goalLabel} ${split.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())} Program`,
        content,
        goal,
        split,
        equipment,
      };
      await saveAiWorkout(payload);
      setSaveMsg("Workout saved to archive!");
      setTimeout(() => setSaveMsg(null), 3000);
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const hasContent = content.length > 0;

  return (
    <div className="space-y-6">
      {/* Form Card */}
      <div className="rounded-2xl border border-white/10 bg-[#12121A]/80 p-6 backdrop-blur-xl">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-[#8A8A94]">
          AI Workout Generator
        </p>
        <h1 className="mt-2 text-xl font-semibold text-white">
          Build Your Program
        </h1>
        <p className="mt-2 text-[#8A8A94]">
          Generate a structured, progressive workout routine tailored to your goals.
        </p>

        {/* Goal selector */}
        <div className="mt-6 space-y-2">
          <label className="text-sm font-medium text-[#C4C4CC]">Goal</label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {goals.map((g) => (
              <button
                key={g.value}
                onClick={() => setGoal(g.value)}
                className={`rounded-xl border p-3 text-left transition-all ${
                  goal === g.value
                    ? "border-[#DC143C]/40 bg-[#DC143C]/10 text-white"
                    : "border-white/10 bg-white/3 text-[#8A8A94] hover:bg-white/5"
                }`}
              >
                <span className="text-lg">{g.icon}</span>
                <p className="mt-1 text-sm font-medium">{g.label}</p>
                <p className="text-xs text-[#5A5A64]">{g.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Experience + Split + Equipment row */}
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[#C4C4CC]">Experience</label>
            <div className="space-y-1.5">
              {experienceLevels.map((e) => (
                <button
                  key={e.value}
                  onClick={() => setExperience(e.value)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                    experience === e.value
                      ? "border-white/20 bg-white/8 text-white"
                      : "border-white/10 bg-white/3 text-[#8A8A94] hover:bg-white/5"
                  }`}
                >
                  {e.label}{" "}
                  <span className="text-[#5A5A64]">· {e.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[#C4C4CC]">Split</label>
            <div className="space-y-1.5">
              {splits.map((s) => (
                <button
                  key={s.value}
                  onClick={() => setSplit(s.value)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                    split === s.value
                      ? "border-white/20 bg-white/8 text-white"
                      : "border-white/10 bg-white/3 text-[#8A8A94] hover:bg-white/5"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[#C4C4CC]">Equipment</label>
            <div className="space-y-1.5">
              {equipmentOptions.map((eq) => (
                <button
                  key={eq.value}
                  onClick={() => setEquipment(eq.value)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                    equipment === eq.value
                      ? "border-white/20 bg-white/8 text-white"
                      : "border-white/10 bg-white/3 text-[#8A8A94] hover:bg-white/5"
                  }`}
                >
                  <span className="mr-1.5">{eq.icon}</span>
                  {eq.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Generate button */}
        <div className="mt-6 flex items-center gap-3">
          {isStreaming ? (
            <Button
              onClick={abort}
              variant="outline"
              className="border-white/20 bg-white/5"
            >
              Stop Generation
            </Button>
          ) : (
            <Button onClick={handleGenerate} className="btn-chrome-accent">
              Generate Workout
            </Button>
          )}
        </div>
      </div>

      {/* Sandbox banner */}
      {isSandbox && (
        <div className="rounded-2xl border border-[#F59E0B]/20 bg-[#F59E0B]/5 px-4 py-3">
          <p className="flex items-center gap-2 text-sm font-medium text-[#F59E0B]">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#F59E0B]" />
            Using offline AI model (Sandbox mode) — add OPENAI_API_KEY for live generation
          </p>
        </div>
      )}

      {/* Error */}
      {error && !isSandbox && (
        <div className="rounded-2xl border border-[#DC143C]/20 bg-[#DC143C]/5 p-4 text-sm text-[#FF6B3D]">
          {error}
        </div>
      )}

      {/* Streaming Output */}
      {(hasContent || isStreaming) && (
        <div className="rounded-2xl border border-white/10 bg-[#12121A]/80 backdrop-blur-xl">
          {/* Terminal header */}
          <div className="flex items-center justify-between border-b border-white/8 px-5 py-3">
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-[#DC143C]/60" />
              <div className="h-2.5 w-2.5 rounded-full bg-[#F59E0B]/60" />
              <div className="h-2.5 w-2.5 rounded-full bg-[#10B981]/60" />
              <span className="ml-2 text-xs text-[#5A5A64]">AI Workout Generator</span>
            </div>
            <div className="flex items-center gap-2">
              {isStreaming && (
                <span className="flex items-center gap-1.5 text-xs text-[#DC143C]">
                  <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-[#DC143C]" />
                  streaming
                </span>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="max-h-[600px] overflow-y-auto p-6">
            {isStreaming && !hasContent && (
              <p className="text-sm text-[#8A8A94]">Generating your workout program...</p>
            )}
            {hasContent && (
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Action toolbar */}
          {hasContent && !isStreaming && (
            <div className="flex items-center gap-3 border-t border-white/8 px-5 py-3">
              <Button
                onClick={handleSave}
                disabled={saving}
                size="sm"
                className="btn-chrome-accent"
              >
                {saving ? "Saving..." : "Save to Archive"}
              </Button>
              <Button onClick={handleCopy} variant="outline" size="sm" className="border-white/10 bg-white/3">
                Copy Markdown
              </Button>
              <Button onClick={reset} variant="outline" size="sm" className="border-white/10 bg-white/3">
                Regenerate
              </Button>
              {saveMsg && (
                <span className="ml-auto text-xs text-[#8A8A94]">{saveMsg}</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
