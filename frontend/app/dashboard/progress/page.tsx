"use client";

import { useEffect, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  createProgressEntry,
  getProgress,
  getProgressSummary,
  type ProgressEntry,
  type ProgressEntryCreate,
  type ProgressSummary,
} from "@/lib/api";

/* ── State types ────────────────────────────────────────────────────────── */

type SummaryState =
  | { status: "loading" }
  | { status: "ready"; data: ProgressSummary }
  | { status: "error"; message: string };

type HistoryState =
  | { status: "loading" }
  | { status: "ready"; entries: ProgressEntry[] }
  | { status: "error"; message: string };

/* ── Goal labels ────────────────────────────────────────────────────────── */

const goalLabels: Record<string, string> = {
  weight_loss: "Weight Loss",
  weight_gain: "Weight Gain",
  muscle_building: "Muscle Building",
  general_fitness: "General Fitness",
};

/* ── Page ───────────────────────────────────────────────────────────────── */

export default function ProgressPage() {
  const [summary, setSummary] = useState<SummaryState>({ status: "loading" });
  const [history, setHistory] = useState<HistoryState>({ status: "loading" });
  const [formSuccess, setFormSuccess] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadSummary = () => {
    getProgressSummary()
      .then((data) => setSummary({ status: "ready", data }))
      .catch((err: unknown) =>
        setSummary({
          status: "error",
          message: err instanceof Error ? err.message : "Failed to load summary.",
        }),
      );
  };

  const loadHistory = () => {
    getProgress()
      .then((entries) => setHistory({ status: "ready", entries }))
      .catch((err: unknown) =>
        setHistory({
          status: "error",
          message: err instanceof Error ? err.message : "Failed to load history.",
        }),
      );
  };

  useEffect(() => {
    loadSummary();
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleEntryCreated = () => {
    setFormSuccess(true);
    setFormError(null);
    loadSummary();
    loadHistory();
    setTimeout(() => setFormSuccess(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
          Progress
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Track Your Progress
        </h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Log your weight and measurements to see how you&apos;re progressing
          toward your fitness goal.
        </p>
      </div>

      {formSuccess && (
        <AlertBanner variant="info" message="Progress entry saved successfully." />
      )}

      {formError && (
        <AlertBanner variant="error" message={formError} />
      )}

      {/* Summary + Form row */}
      <div className="grid gap-4 md:grid-cols-2">
        <SummaryCard state={summary} />
        <LogForm
          onError={setFormError}
          onCreated={handleEntryCreated}
        />
      </div>

      {/* History */}
      <HistorySection state={history} />
    </div>
  );
}

/* ── Summary Card ───────────────────────────────────────────────────────── */

function SummaryCard({ state }: { state: SummaryState }) {
  if (state.status === "loading") {
    return <Skeleton className="h-64 rounded-2xl" />;
  }

  if (state.status === "error") {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
          Summary
        </p>
        <AlertBanner variant="error" message={state.message} className="mt-4" />
      </div>
    );
  }

  const d = state.data;
  const hasEntries = d.entry_count > 0;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
        Summary
      </p>

      {!hasEntries ? (
        <p className="mt-4 text-slate-600">
          No progress entries yet. Log your first weight to start tracking.
        </p>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-2 gap-4">
            <StatBlock
              label="Starting"
              value={d.starting_weight_kg != null ? `${d.starting_weight_kg} kg` : "—"}
            />
            <StatBlock
              label="Current"
              value={d.current_weight_kg != null ? `${d.current_weight_kg} kg` : "—"}
            />
            <StatBlock
              label="Change"
              value={formatWeightChange(d.weight_change_kg)}
              highlight={d.weight_change_kg != null && d.weight_change_kg !== 0}
              positive={d.weight_change_kg != null && d.weight_change_kg > 0}
              negative={d.weight_change_kg != null && d.weight_change_kg < 0}
            />
            <StatBlock
              label="BMI"
              value={d.bmi != null ? `${d.bmi}` : "—"}
            />
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <StatBlock
              label="Goal"
              value={d.fitness_goal ? (goalLabels[d.fitness_goal] ?? d.fitness_goal) : "—"}
            />
            <StatBlock
              label="Entries"
              value={`${d.entry_count}`}
            />
          </div>

          {d.height_cm != null && (
            <p className="mt-3 text-xs text-slate-500">
              Height: {d.height_cm} cm
            </p>
          )}
        </>
      )}
    </div>
  );
}

function StatBlock({
  label,
  value,
  highlight,
  positive,
  negative,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  positive?: boolean;
  negative?: boolean;
}) {
  let valueClass = "text-slate-900";
  if (highlight && positive) valueClass = "text-emerald-700";
  if (highlight && negative) valueClass = "text-rose-600";

  return (
    <div className="rounded-xl bg-slate-50 px-4 py-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-lg font-semibold ${valueClass}`}>{value}</p>
    </div>
  );
}

function formatWeightChange(change: number | null): string {
  if (change == null) return "—";
  if (change === 0) return "0 kg";
  const sign = change > 0 ? "+" : "";
  return `${sign}${change} kg`;
}

/* ── Log Form ───────────────────────────────────────────────────────────── */

function LogForm({
  onError,
  onCreated,
}: {
  onError: (msg: string | null) => void;
  onCreated: () => void;
}) {
  const today = new Date().toISOString().split("T")[0];
  const [date, setDate] = useState(today);
  const [weight, setWeight] = useState("");
  const [waist, setWaist] = useState("");
  const [hip, setHip] = useState("");
  const [bodyFat, setBodyFat] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onError(null);

    const weightVal = parseFloat(weight);
    if (isNaN(weightVal) || weightVal <= 0) {
      onError("Please enter a valid weight greater than 0.");
      return;
    }

    const payload: ProgressEntryCreate = {
      recorded_on: date,
      weight_kg: weightVal,
    };

    const waistVal = parseFloat(waist);
    if (!isNaN(waistVal) && waistVal > 0) payload.waist_cm = waistVal;

    const hipVal = parseFloat(hip);
    if (!isNaN(hipVal) && hipVal > 0) payload.hip_cm = hipVal;

    const bfVal = parseFloat(bodyFat);
    if (!isNaN(bfVal) && bfVal >= 0 && bfVal <= 100) {
      payload.body_fat_percent = bfVal;
    }

    if (notes.trim()) payload.notes = notes.trim();

    setSubmitting(true);
    try {
      await createProgressEntry(payload);
      // Reset form
      setWeight("");
      setWaist("");
      setHip("");
      setBodyFat("");
      setNotes("");
      onCreated();
    } catch (err: unknown) {
      onError(err instanceof Error ? err.message : "Failed to save entry.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
        Log Progress
      </p>
      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <div>
          <label htmlFor="progress-date" className="block text-sm font-medium text-slate-700">
            Date
          </label>
          <input
            id="progress-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            required
          />
        </div>

        <div>
          <label htmlFor="progress-weight" className="block text-sm font-medium text-slate-700">
            Weight (kg) *
          </label>
          <input
            id="progress-weight"
            type="number"
            step="0.1"
            min="1"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            placeholder="e.g. 72.5"
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="progress-waist" className="block text-sm font-medium text-slate-700">
              Waist (cm)
            </label>
            <input
              id="progress-waist"
              type="number"
              step="0.1"
              min="0"
              value={waist}
              onChange={(e) => setWaist(e.target.value)}
              placeholder="Optional"
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label htmlFor="progress-hip" className="block text-sm font-medium text-slate-700">
              Hip (cm)
            </label>
            <input
              id="progress-hip"
              type="number"
              step="0.1"
              min="0"
              value={hip}
              onChange={(e) => setHip(e.target.value)}
              placeholder="Optional"
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>

        <div>
          <label htmlFor="progress-bodyfat" className="block text-sm font-medium text-slate-700">
            Body Fat (%)
          </label>
          <input
            id="progress-bodyfat"
            type="number"
            step="0.1"
            min="0"
            max="100"
            value={bodyFat}
            onChange={(e) => setBodyFat(e.target.value)}
            placeholder="Optional"
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label htmlFor="progress-notes" className="block text-sm font-medium text-slate-700">
            Notes
          </label>
          <textarea
            id="progress-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes"
            rows={2}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <Button type="submit" disabled={submitting} className="w-full">
          {submitting ? "Saving…" : "Save Entry"}
        </Button>
      </form>
    </div>
  );
}

/* ── History Section ────────────────────────────────────────────────────── */

function HistorySection({ state }: { state: HistoryState }) {
  if (state.status === "loading") {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
          Weight History
        </p>
        <div className="mt-4 space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
          Weight History
        </p>
        <AlertBanner variant="error" message={state.message} className="mt-4" />
      </div>
    );
  }

  const { entries } = state;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">
        Weight History
      </p>

      {entries.length === 0 ? (
        <p className="mt-4 text-slate-600">
          No entries yet. Use the form above to log your first measurement.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-medium text-slate-500">
                <th className="pb-2 pr-4">Date</th>
                <th className="pb-2 pr-4">Weight</th>
                <th className="pb-2 pr-4 hidden sm:table-cell">Change</th>
                <th className="pb-2 pr-4 hidden md:table-cell">Waist</th>
                <th className="pb-2 pr-4 hidden md:table-cell">Hip</th>
                <th className="pb-2 pr-4 hidden lg:table-cell">BF%</th>
                <th className="pb-2 hidden lg:table-cell">Notes</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, idx) => {
                const prev = entries[idx + 1];
                const change = prev
                  ? Number(entry.weight_kg) - Number(prev.weight_kg)
                  : null;
                return (
                  <tr
                    key={entry.id}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="py-3 pr-4 font-medium text-slate-900">
                      {formatDate(entry.recorded_on)}
                    </td>
                    <td className="py-3 pr-4 text-slate-900">
                      {entry.weight_kg} kg
                    </td>
                    <td className="py-3 pr-4 hidden sm:table-cell">
                      {change != null ? (
                        <span
                          className={
                            change < 0
                              ? "text-emerald-600"
                              : change > 0
                                ? "text-rose-600"
                                : "text-slate-500"
                          }
                        >
                          {change > 0 ? "+" : ""}
                          {change.toFixed(1)} kg
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 hidden md:table-cell text-slate-600">
                      {entry.waist_cm != null ? `${entry.waist_cm} cm` : "—"}
                    </td>
                    <td className="py-3 pr-4 hidden md:table-cell text-slate-600">
                      {entry.hip_cm != null ? `${entry.hip_cm} cm` : "—"}
                    </td>
                    <td className="py-3 pr-4 hidden lg:table-cell text-slate-600">
                      {entry.body_fat_percent != null ? `${entry.body_fat_percent}%` : "—"}
                    </td>
                    <td className="py-3 hidden lg:table-cell text-slate-500 max-w-[200px] truncate">
                      {entry.notes ?? "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function formatDate(isoDate: string): string {
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
