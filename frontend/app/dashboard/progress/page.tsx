"use client";

import { useEffect, useState } from "react";

import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  createProgressEntry,
  deleteProgressEntry,
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
  const [deleteMsg, setDeleteMsg] = useState<{
    type: "info" | "error";
    text: string;
  } | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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
    // eslint-disable-line react-hooks/exhaustive-deps
  }, []);

  const handleEntryCreated = () => {
    setFormSuccess(true);
    setFormError(null);
    loadSummary();
    loadHistory();
    setTimeout(() => setFormSuccess(false), 3000);
  };

  const handleDelete = async (entryId: string) => {
    setDeletingId(entryId);
    setDeleteMsg(null);
    try {
      await deleteProgressEntry(entryId);
      setDeleteMsg({ type: "info", text: "Entry deleted." });
      loadSummary();
      loadHistory();
    } catch (err: unknown) {
      setDeleteMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to delete entry.",
      });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl glass p-6">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
          Progress
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-stone-900">
          Track Your Progress
        </h1>
        <p className="mt-2 max-w-2xl text-stone-500">
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

      {deleteMsg && (
        <AlertBanner variant={deleteMsg.type} message={deleteMsg.text} />
      )}

      {/* Summary + Form row */}
      <div className="grid gap-4 md:grid-cols-2">
        <SummaryCard state={summary} />
        <LogForm onError={setFormError} onCreated={handleEntryCreated} />
      </div>

      {/* Weight Trend Chart */}
      <WeightChart state={history} />

      {/* History */}
      <HistorySection
        state={history}
        onDelete={handleDelete}
        deletingId={deletingId}
      />
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
      <div className="rounded-2xl glass p-6">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
          Summary
        </p>
        <AlertBanner variant="error" message={state.message} className="mt-4" />
      </div>
    );
  }

  const d = state.data;
  const hasEntries = d.entry_count > 0;

  return (
    <div className="rounded-2xl glass p-6">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
        Summary
      </p>

      {!hasEntries ? (
        <p className="mt-4 text-stone-500">
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
            <p className="mt-3 text-xs text-stone-500">
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
  let valueClass = "text-stone-900";
  if (highlight && positive) valueClass = "text-[#FF6B3D]";
  if (highlight && !positive) valueClass = "text-[#34D399]";
  if (highlight && negative) valueClass = "text-rose-600";

  return (
    <div className="rounded-xl bg-stone-50 px-4 py-3">
      <p className="text-xs text-stone-500">{label}</p>
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

/* ── Weight Trend Chart ─────────────────────────────────────────────────── */

function WeightChart({ state }: { state: HistoryState }) {
  if (state.status === "loading") {
    return <Skeleton className="h-64 rounded-2xl" />;
  }

  if (state.status === "error" || state.entries.length < 2) {
    return null; // Don't show chart with fewer than 2 data points
  }

  // Entries are newest first; reverse for chart (oldest → newest)
  const chartData = [...state.entries]
    .reverse()
    .map((e) => ({
      date: formatChartDate(e.recorded_on),
      weight: Number(e.weight_kg),
    }));

  return (
    <div className="rounded-2xl glass p-6">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
        Weight Trend
      </p>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="weightGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: "#64748b" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#64748b" }}
              tickLine={false}
              axisLine={false}
              width={45}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                fontSize: "13px",
              }}
              formatter={(value) => [`${String(value)} kg`, "Weight"]}
            />
            <Area
              type="monotone"
              dataKey="weight"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#weightGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function formatChartDate(isoDate: string): string {
  try {
    return new Date(isoDate + "T00:00:00").toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return isoDate;
  }
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
    <div className="rounded-2xl glass p-6">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
        Log Progress
      </p>
      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <div>
          <label htmlFor="progress-date" className="block text-sm font-medium text-stone-600">
            Date
          </label>
          <input
            id="progress-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-1 block w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-sm text-stone-900 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
            required
          />
        </div>

        <div>
          <label htmlFor="progress-weight" className="block text-sm font-medium text-stone-600">
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
            className="mt-1 block w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-sm text-stone-900 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="progress-waist" className="block text-sm font-medium text-stone-600">
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
              className="mt-1 block w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-sm text-stone-900 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
            />
          </div>
          <div>
            <label htmlFor="progress-hip" className="block text-sm font-medium text-stone-600">
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
              className="mt-1 block w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-sm text-stone-900 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
            />
          </div>
        </div>

        <div>
          <label htmlFor="progress-bodyfat" className="block text-sm font-medium text-stone-600">
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
            className="mt-1 block w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-sm text-stone-900 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
          />
        </div>

        <div>
          <label htmlFor="progress-notes" className="block text-sm font-medium text-stone-600">
            Notes
          </label>
          <textarea
            id="progress-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes"
            rows={2}
            className="mt-1 block w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-sm text-stone-900 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
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

function HistorySection({
  state,
  onDelete,
  deletingId,
}: {
  state: HistoryState;
  onDelete: (id: string) => void;
  deletingId: string | null;
}) {
  if (state.status === "loading") {
    return (
      <div className="rounded-2xl glass p-6">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
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
      <div className="rounded-2xl glass p-6">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
          Weight History
        </p>
        <AlertBanner variant="error" message={state.message} className="mt-4" />
      </div>
    );
  }

  const { entries } = state;

  return (
    <div className="rounded-2xl glass p-6">
      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-stone-500">
        Weight History
      </p>

      {entries.length === 0 ? (
        <p className="mt-4 text-stone-500">
          No entries yet. Use the form above to log your first measurement.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-stone-200 text-xs font-medium text-stone-500">
                <th className="pb-2 pr-4">Date</th>
                <th className="pb-2 pr-4">Weight</th>
                <th className="pb-2 pr-4 hidden sm:table-cell">Change</th>
                <th className="pb-2 pr-4 hidden md:table-cell">Waist</th>
                <th className="pb-2 pr-4 hidden md:table-cell">Hip</th>
                <th className="pb-2 pr-4 hidden lg:table-cell">BF%</th>
                <th className="pb-2 pr-4 hidden lg:table-cell">Notes</th>
                <th className="pb-2 text-right">Action</th>
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
                    className="border-b border-stone-200 last:border-0"
                  >
                    <td className="py-3 pr-4 font-medium text-stone-900">
                      {formatDate(entry.recorded_on)}
                    </td>
                    <td className="py-3 pr-4 text-stone-900">
                      {entry.weight_kg} kg
                    </td>
                    <td className="py-3 pr-4 hidden sm:table-cell">
                      {change != null ? (
                        <span
                          className={
                            change < 0
                              ? "text-stone-900"
                              : change > 0
                                ? "text-rose-600"
                                : "text-stone-500"
                          }
                        >
                          {change > 0 ? "+" : ""}
                          {change.toFixed(1)} kg
                        </span>
                      ) : (
                        <span className="text-stone-500">—</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 hidden md:table-cell text-stone-500">
                      {entry.waist_cm != null ? `${entry.waist_cm} cm` : "—"}
                    </td>
                    <td className="py-3 pr-4 hidden md:table-cell text-stone-500">
                      {entry.hip_cm != null ? `${entry.hip_cm} cm` : "—"}
                    </td>
                    <td className="py-3 pr-4 hidden lg:table-cell text-stone-500">
                      {entry.body_fat_percent != null ? `${entry.body_fat_percent}%` : "—"}
                    </td>
                    <td className="py-3 pr-4 hidden lg:table-cell text-stone-500 max-w-[200px] truncate">
                      {entry.notes ?? "—"}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => onDelete(entry.id)}
                        disabled={deletingId === entry.id}
                        className="text-xs font-medium text-rose-500 hover:text-rose-700 disabled:opacity-50"
                      >
                        {deletingId === entry.id ? "..." : "Delete"}
                      </button>
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
