"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  fetchLocations,
  submitOnboarding,
  type CountryData,
} from "@/lib/api";

/* ── Activity Levels ──────────────────────────────────────────────────── */

const activityLevels = [
  {
    value: "sedentary",
    label: "Sedentary",
    desc: "Desk job, little exercise",
    multiplier: "1.2×",
  },
  {
    value: "lightly_active",
    label: "Lightly Active",
    desc: "Light walks, occasional exercise",
    multiplier: "1.375×",
  },
  {
    value: "moderately_active",
    label: "Moderately Active",
    desc: "Regular exercise 3–5×/week",
    multiplier: "1.55×",
  },
  {
    value: "very_active",
    label: "Very Active",
    desc: "Intense exercise 6–7×/week",
    multiplier: "1.725×",
  },
  {
    value: "extra_active",
    label: "Extra Active",
    desc: "Athlete-level training",
    multiplier: "1.9×",
  },
] as const;

/* ── Fitness Goals ────────────────────────────────────────────────────── */

const fitnessGoals = [
  {
    value: "weight_loss",
    label: "Cut",
    icon: "🔥",
    desc: "Lose body fat while preserving muscle",
    tagline: "Shed fat. Stay strong.",
    calAdj: "-500 kcal",
  },
  {
    value: "weight_gain",
    label: "Bulk",
    icon: "💪",
    desc: "Gain weight and mass progressively",
    tagline: "Build mass. Fuel growth.",
    calAdj: "+400 kcal",
  },
  {
    value: "muscle_building",
    label: "Recomp",
    icon: "⚡",
    desc: "Build muscle while managing fat",
    tagline: "Sculpt. Define. Perform.",
    calAdj: "+300 kcal",
  },
  {
    value: "general_fitness",
    label: "Maintain",
    icon: "🌿",
    desc: "Stay healthy and maintain current physique",
    tagline: "Balance. Consistency. Life.",
    calAdj: "0 kcal",
  },
] as const;

/* ── Diet Patterns ────────────────────────────────────────────────────── */

const dietPatterns = [
  { value: "omnivore", label: "Omnivore", desc: "I eat everything" },
  { value: "vegetarian", label: "Vegetarian", desc: "No meat, fish, or poultry" },
  { value: "eggetarian", label: "Eggetarian", desc: "Vegetarian + eggs" },
  { value: "vegan", label: "Vegan", desc: "No animal products" },
  { value: "pescetarian", label: "Pescetarian", desc: "Vegetarian + fish" },
] as const;

/* ── Types ────────────────────────────────────────────────────────────── */

type GoalValue = (typeof fitnessGoals)[number]["value"];
type ActivityValue = (typeof activityLevels)[number]["value"];
type DietValue = (typeof dietPatterns)[number]["value"];
type SexValue = "female" | "male" | "other";

type FormState = {
  country_id: string;
  region_id: string;
  preferred_currency_code: string;
  preferred_language: string;
  unit_system: "metric" | "imperial";
  age_years: string;
  sex: SexValue;
  height_cm: string;
  weight_kg: string;
  activity_level: ActivityValue;
  fitness_goal: GoalValue;
  diet_pattern: DietValue;
  dietary_tag_slugs: string;
  allergen_tag_slugs: string;
  food_dislikes: string;
  preferred_foods: string;
  weekly_budget_amount: string;
  budget_period: string;
};

const initialForm: FormState = {
  country_id: "",
  region_id: "",
  preferred_currency_code: "PKR",
  preferred_language: "en",
  unit_system: "metric",
  age_years: "28",
  sex: "female",
  height_cm: "165",
  weight_kg: "62",
  activity_level: "moderately_active",
  fitness_goal: "weight_loss",
  diet_pattern: "omnivore",
  dietary_tag_slugs: "",
  allergen_tag_slugs: "",
  food_dislikes: "",
  preferred_foods: "",
  weekly_budget_amount: "",
  budget_period: "weekly",
};

/* ── Helpers ──────────────────────────────────────────────────────────── */

function parseList(values: string) {
  return values.split(",").map((v) => v.trim()).filter(Boolean);
}

/** Client-side TDEE preview (same formula as backend). */
function calcPreview(form: FormState) {
  const age = Number(form.age_years) || 28;
  const h = Number(form.height_cm) || 170;
  const w = Number(form.weight_kg) || 70;
  const sex = form.sex;

  let bmr: number;
  if (sex === "male") {
    bmr = 10 * w + 6.25 * h - 5 * age - 5;
  } else if (sex === "female") {
    bmr = 10 * w + 6.25 * h - 5 * age - 161;
  } else {
    const bm = 10 * w + 6.25 * h - 5 * age - 5;
    const bf = 10 * w + 6.25 * h - 5 * age - 161;
    bmr = (bm + bf) / 2;
  }

  const mult: Record<string, number> = {
    sedentary: 1.2, lightly_active: 1.375, moderately_active: 1.55,
    very_active: 1.725, extra_active: 1.9,
  };
  const adj: Record<string, number> = {
    weight_loss: -500, weight_gain: 400, muscle_building: 300, general_fitness: 0,
  };

  const tdee = bmr * (mult[form.activity_level] ?? 1.55);
  const calTarget = tdee + (adj[form.fitness_goal] ?? 0);
  const protein = w * 1.8;

  return {
    bmr: Math.round(bmr),
    tdee: Math.round(tdee),
    target_calories: Math.max(1000, Math.min(6000, Math.round(calTarget))),
    protein_g: Math.round(protein),
  };
}

/* ── Animation Helpers ────────────────────────────────────────────────── */

function FadeSlide({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.opacity = "0";
    el.style.transform = "translateY(32px)";
    const raf = requestAnimationFrame(() => {
      el.style.transition = "opacity 0.5s cubic-bezier(.16,1,.3,1), transform 0.5s cubic-bezier(.16,1,.3,1)";
      el.style.opacity = "1";
      el.style.transform = "translateY(0)";
    });
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────────────────── */

export function OnboardingWizard() {
  const router = useRouter();
  const [stepIndex, setStepIndex] = useState(0);
  const [form, setForm] = useState<FormState>(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState<{
    target_calories: number;
    target_protein_g: number;
  } | null>(null);

  /* ── Locations ──────────────────────────────────────────────────────── */
  const [countries, setCountries] = useState<CountryData[]>([]);
  const [locationsLoading, setLocationsLoading] = useState(true);
  const [locationsError, setLocationsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchLocations();
        if (cancelled) return;
        setCountries(data);
        if (data.length > 0 && !form.country_id) {
          setForm((c) => ({
            ...c,
            country_id: data[0].id,
            preferred_currency_code: data[0].currency_code,
          }));
        }
      } catch (err) {
        if (!cancelled) {
          setLocationsError(err instanceof Error ? err.message : "Unable to load countries.");
        }
      } finally {
        if (!cancelled) setLocationsLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedCountry = countries.find((c) => c.id === form.country_id);
  const currentRegions = selectedCountry?.regions ?? [];

  const updateField = <K extends keyof FormState>(field: K, value: FormState[K]) => {
    setForm((c) => ({ ...c, [field]: value }));
  };

  const handleSelect = (event: ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = event.target;
    if (name === "country_id") {
      const newCountry = countries.find((c) => c.id === value);
      setForm((c) => ({
        ...c,
        country_id: value,
        region_id: "",
        preferred_currency_code: newCountry?.currency_code ?? c.preferred_currency_code,
      }));
      return;
    }
    updateField(name as keyof FormState, value as never);
  };

  /* ── Live preview ───────────────────────────────────────────────────── */
  const preview = calcPreview(form);

  /* ── Validation ─────────────────────────────────────────────────────── */
  const validateStep = (): string | null => {
    if (stepIndex === 0) return null; // goal
    if (stepIndex === 1) {
      if (!form.age_years || Number(form.age_years) <= 0) return "Enter a valid age.";
      if (!form.height_cm || Number(form.height_cm) <= 0) return "Enter a valid height.";
      if (!form.weight_kg || Number(form.weight_kg) <= 0) return "Enter a valid weight.";
      return null;
    }
    if (stepIndex === 2) return null; // activity
    if (stepIndex === 3) {
      if (!form.country_id) return "Choose a country.";
      return null;
    }
    if (stepIndex === 4) return null; // diet
    if (stepIndex === 5) return null; // preferences
    return null; // budget
  };

  /* ── Navigation ─────────────────────────────────────────────────────── */
  const canGoBack = stepIndex > 0;
  const isLastStep = stepIndex === 6;
  const totalSteps = 7;

  const handleNext = () => {
    const err = validateStep();
    if (err) { setError(err); return; }
    setError(null);
    if (isLastStep) { void submitForm(); return; }
    setStepIndex((c) => c + 1);
  };

  const handleBack = () => {
    setError(null);
    setStepIndex((c) => Math.max(0, c - 1));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) {
      e.preventDefault();
      handleNext();
    }
  };

  /* ── Submit ─────────────────────────────────────────────────────────── */
  const submitForm = async () => {
    setError(null);
    setCalculating(true);
    try {
      const response = await submitOnboarding({
        country_id: form.country_id,
        region_id: form.region_id || null,
        preferred_currency_code: form.preferred_currency_code.trim().slice(0, 3).toUpperCase(),
        preferred_language: form.preferred_language.trim() || "en",
        unit_system: form.unit_system,
        age_years: Number(form.age_years),
        sex: form.sex,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        activity_level: form.activity_level,
        fitness_goal: form.fitness_goal,
        diet_pattern: form.diet_pattern,
        dietary_tag_slugs: parseList(form.dietary_tag_slugs),
        allergen_tag_slugs: parseList(form.allergen_tag_slugs),
        food_dislikes: parseList(form.food_dislikes),
        preferred_foods: parseList(form.preferred_foods),
        weekly_budget_amount: Number(form.weekly_budget_amount) || 0,
        budget_period: form.budget_period,
      });

      // Show result
      setResult({
        target_calories: response.target_calories ?? preview.target_calories,
        target_protein_g: response.target_protein_g ?? preview.protein_g,
      });
      setCalculating(false);

      // Brief delay to admire the results, then redirect
      setTimeout(() => {
        router.push("/dashboard");
        router.refresh();
      }, 2500);
    } catch (caughtError) {
      setCalculating(false);
      setError(
        caughtError instanceof Error ? caughtError.message : "Unable to save onboarding details.",
      );
    }
  };

  /* ── Step content ───────────────────────────────────────────────────── */

  const selectClass =
    "w-full rounded-xl border border-white/10 bg-white/[0.05] px-3.5 py-2.5 text-white placeholder:text-zinc-400 outline-none transition-all focus:border-white/50 focus:ring-1 focus:ring-indigo-500/30";

  const renderStep = () => {
    // ─── Step 0: Goal Selection ────────────────────────────────────────
    if (stepIndex === 0) {
      return (
        <FadeSlide>
          <div className="grid gap-4 sm:grid-cols-2">
            {fitnessGoals.map((g) => (
              <button
                key={g.value}
                type="button"
                onClick={() => updateField("fitness_goal", g.value as GoalValue)}
                className={`group relative overflow-hidden rounded-2xl border p-6 text-left transition-all duration-300 ${
                  form.fitness_goal === g.value
                    ? "border-white/60 bg-white/10 shadow-[0_0_30px_rgba(220,20,60,0.15)]"
                    : "border-white/10 bg-white/[0.04] hover:border-white/[0.12] hover:bg-white/[0.06]"
                }`}
              >
                {form.fitness_goal === g.value && (
                  <div className="absolute inset-0 bg-gradient-to-br from-zinc-700/5 to-transparent" />
                )}
                <div className="relative">
                  <div className="mb-3 text-3xl">{g.icon}</div>
                  <h3 className="text-lg font-semibold text-white">{g.label}</h3>
                  <p className="mt-1 text-sm text-zinc-400">{g.tagline}</p>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="rounded-md bg-white/[0.06] px-2 py-0.5 text-xs font-medium text-zinc-400">
                      {g.calAdj}
                    </span>
                    <span className="text-xs text-zinc-400">{g.desc}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </FadeSlide>
      );
    }

    // ─── Step 1: Body Metrics ──────────────────────────────────────────
    if (stepIndex === 1) {
      return (
        <FadeSlide>
          <div className="space-y-6">
            <div className="grid gap-5 sm:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Age</label>
                <input
                  type="number"
                  min={13}
                  max={120}
                  value={form.age_years}
                  onChange={(e) => updateField("age_years", e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-center text-2xl font-bold text-white outline-none transition-all focus:border-white/50 focus:ring-1 focus:ring-indigo-500/30"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Height (cm)</label>
                <input
                  type="number"
                  value={form.height_cm}
                  onChange={(e) => updateField("height_cm", e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-center text-2xl font-bold text-white outline-none transition-all focus:border-white/50 focus:ring-1 focus:ring-indigo-500/30"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Weight (kg)</label>
                <input
                  type="number"
                  value={form.weight_kg}
                  onChange={(e) => updateField("weight_kg", e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3 text-center text-2xl font-bold text-white outline-none transition-all focus:border-white/50 focus:ring-1 focus:ring-indigo-500/30"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Sex</label>
              <div className="flex gap-3">
                {(["female", "male", "other"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => updateField("sex", s)}
                    className={`flex-1 rounded-xl border px-4 py-2.5 text-sm font-medium transition-all ${
                      form.sex === s
                        ? "border-white/60 bg-white/10 text-white"
                        : "border-white/10 bg-white/[0.04] text-zinc-400 hover:border-white/[0.12]"
                    }`}
                  >
                    {s.charAt(0).toUpperCase() + s.slice(1).replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            {/* Live TDEE Preview */}
            <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-zinc-400 mb-3">
                Live Preview
              </p>
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-white">{preview.bmr}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">BMR kcal</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-zinc-400">{preview.tdee}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">TDEE kcal</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{preview.target_calories}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">Target kcal</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{preview.protein_g}g</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">Protein</p>
                </div>
              </div>
            </div>
          </div>
        </FadeSlide>
      );
    }

    // ─── Step 2: Activity Level ────────────────────────────────────────
    if (stepIndex === 2) {
      return (
        <FadeSlide>
          <div className="space-y-3">
            {activityLevels.map((a) => (
              <button
                key={a.value}
                type="button"
                onClick={() => updateField("activity_level", a.value as ActivityValue)}
                className={`w-full rounded-xl border p-4 text-left transition-all duration-200 ${
                  form.activity_level === a.value
                    ? "border-white/60 bg-white/10"
                    : "border-white/10 bg-white/[0.04] hover:border-white/[0.12] hover:bg-white/[0.06]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">{a.label}</p>
                    <p className="text-sm text-zinc-400">{a.desc}</p>
                  </div>
                  <span className="rounded-lg bg-white/[0.06] px-2.5 py-1 text-xs font-mono text-zinc-400">
                    {a.multiplier}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </FadeSlide>
      );
    }

    // ─── Step 3: Location ──────────────────────────────────────────────
    if (stepIndex === 3) {
      if (locationsLoading) {
        return (
          <FadeSlide>
            <div className="flex items-center justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span className="ml-3 text-sm text-zinc-400">Loading countries...</span>
            </div>
          </FadeSlide>
        );
      }
      if (locationsError) {
        return (
          <FadeSlide>
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {locationsError}
            </div>
          </FadeSlide>
        );
      }
      return (
        <FadeSlide>
          <div className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Country</label>
              <select
                name="country_id"
                value={form.country_id}
                onChange={handleSelect}
                className={selectClass}
              >
                {countries.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Region / state</label>
              <select
                name="region_id"
                value={form.region_id}
                onChange={(e) => updateField("region_id", e.target.value)}
                className={selectClass}
              >
                <option value="">Select region (optional)</option>
                {currentRegions.map((r) => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Currency</label>
                <input
                  value={form.preferred_currency_code}
                  onChange={(e) => updateField("preferred_currency_code", e.target.value)}
                  className={selectClass}
                  placeholder="PKR"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Unit System</label>
                <select
                  name="unit_system"
                  value={form.unit_system}
                  onChange={(e) => updateField("unit_system", e.target.value as "metric" | "imperial")}
                  className={selectClass}
                >
                  <option value="metric">Metric (kg, cm)</option>
                  <option value="imperial">Imperial (lbs, in)</option>
                </select>
              </div>
            </div>
          </div>
        </FadeSlide>
      );
    }

    // ─── Step 4: Diet Pattern ──────────────────────────────────────────
    if (stepIndex === 4) {
      return (
        <FadeSlide>
          <div className="grid gap-3 sm:grid-cols-2">
            {dietPatterns.map((d) => (
              <button
                key={d.value}
                type="button"
                onClick={() => updateField("diet_pattern", d.value as DietValue)}
                className={`rounded-xl border p-4 text-left transition-all duration-200 ${
                  form.diet_pattern === d.value
                    ? "border-white/60 bg-white/10"
                    : "border-white/10 bg-white/[0.04] hover:border-white/[0.12] hover:bg-white/[0.06]"
                }`}
              >
                <p className="font-medium text-white">{d.label}</p>
                <p className="text-sm text-zinc-400">{d.desc}</p>
              </button>
            ))}
          </div>
        </FadeSlide>
      );
    }

    // ─── Step 5: Food Preferences ──────────────────────────────────────
    if (stepIndex === 5) {
      return (
        <FadeSlide>
          <div className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Foods you like (optional)</label>
              <input
                value={form.preferred_foods}
                onChange={(e) => updateField("preferred_foods", e.target.value)}
                className={selectClass}
                placeholder="rice, dal, chicken, yogurt"
              />
              <p className="text-xs text-zinc-400">Comma-separated</p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Foods you dislike (optional)</label>
              <input
                value={form.food_dislikes}
                onChange={(e) => updateField("food_dislikes", e.target.value)}
                className={selectClass}
                placeholder="fried snacks, excessive sugar"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-400">Allergies / restrictions (optional)</label>
              <input
                value={form.allergen_tag_slugs}
                onChange={(e) => updateField("allergen_tag_slugs", e.target.value)}
                className={selectClass}
                placeholder="nuts, dairy"
              />
            </div>
          </div>
        </FadeSlide>
      );
    }

    // ─── Step 6: Budget ────────────────────────────────────────────────
    return (
      <FadeSlide>
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-400">Weekly budget</label>
            <input
              type="number"
              min={0}
              value={form.weekly_budget_amount}
              onChange={(e) => updateField("weekly_budget_amount", e.target.value)}
              className={selectClass}
              placeholder="2500"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-400">Frequency</label>
            <select
              name="budget_period"
              value={form.budget_period}
              onChange={(e) => updateField("budget_period", e.target.value)}
              className={selectClass}
            >
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
        </div>
      </FadeSlide>
    );
  };

  /* ── Calculating Overlay ────────────────────────────────────────────── */
  if (calculating) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <FadeSlide className="text-center">
          <div className="relative mx-auto mb-8 h-24 w-24">
            <div className="absolute inset-0 animate-spin rounded-full border-2 border-white/20 border-t-[#DC143C]" />
            <div className="absolute inset-2 animate-spin rounded-full border-2 border-zinc-700/20 border-b-[#7B61FF] [animation-direction:reverse] [animation-duration:1.5s]" />
            <div className="absolute inset-0 flex items-center justify-center text-3xl">⚡</div>
          </div>
          <h2 className="font-serif text-3xl font-bold text-white">Calculating your plan</h2>
          <p className="mt-3 text-zinc-400">
            Running Mifflin-St Jeor equations across your profile...
          </p>
        </FadeSlide>
      </div>
    );
  }

  /* ── Result State ───────────────────────────────────────────────────── */
  if (result) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <FadeSlide className="text-center">
          <div className="mb-6 text-5xl">🎯</div>
          <h2 className="font-serif text-4xl font-bold text-white">Your targets are set</h2>
          <div className="mt-8 grid grid-cols-2 gap-6 sm:grid-cols-4">
            <div className="rounded-2xl border border-white/20 bg-white/[0.05] p-5">
              <p className="text-3xl font-bold text-white">{result.target_calories}</p>
              <p className="mt-1 text-xs text-zinc-400">kcal / day</p>
            </div>
            <div className="rounded-2xl border border-white/20 bg-white/[0.05] p-5">
              <p className="text-3xl font-bold text-white">{result.target_protein_g}g</p>
              <p className="mt-1 text-xs text-zinc-400">protein / day</p>
            </div>
          </div>
          <p className="mt-8 text-sm text-zinc-400">Redirecting to your dashboard...</p>
        </FadeSlide>
      </div>
    );
  }

  /* ── Main Form ──────────────────────────────────────────────────────── */
  return (
    <div
      className="flex min-h-screen items-center justify-center bg-[#0a0a0a] px-4 py-8"
      onKeyDown={handleKeyDown}
    >
      <div className="w-full max-w-2xl">
        {/* Header */}
        <FadeSlide key={`header-${stepIndex}`}>
          <div className="mb-10 text-center">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-white/60">
              Step {stepIndex + 1} of {totalSteps}
            </p>
            <h1 className="mt-3 font-serif text-3xl font-bold text-white sm:text-4xl">
              {stepIndex === 0 && "What's your goal?"}
              {stepIndex === 1 && "Tell us about yourself"}
              {stepIndex === 2 && "How active are you?"}
              {stepIndex === 3 && "Where are you based?"}
              {stepIndex === 4 && "Your diet preference"}
              {stepIndex === 5 && "Food preferences"}
              {stepIndex === 6 && "Weekly food budget"}
            </h1>
          </div>
        </FadeSlide>

        {/* Progress */}
        <div className="mb-8 flex gap-1.5" role="progressbar">
          {Array.from({ length: totalSteps }, (_, i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full transition-all duration-500 ${
                i <= stepIndex ? "bg-white" : "bg-white/[0.06]"
              }`}
            />
          ))}
        </div>

        {/* Step Content */}
        <div key={`step-${stepIndex}`} className="min-h-[360px]">
          {renderStep()}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Navigation */}
        <FadeSlide className="mt-8 flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={handleBack}
            disabled={!canGoBack || loading}
            className="rounded-xl border border-white/10 bg-white/[0.04] px-6 py-2.5 text-sm font-medium text-zinc-400 transition-all hover:bg-white/[0.06] disabled:opacity-30"
          >
            Back
          </button>

          <div className="flex items-center gap-3">
            {/* Step counter */}
            <span className="text-xs text-[#3A3A44]">
              {stepIndex + 1}/{totalSteps}
            </span>

            <button
              type="button"
              onClick={handleNext}
              disabled={loading}
              className="relative overflow-hidden rounded-xl bg-gradient-to-r from-zinc-700 to-zinc-800 px-8 py-2.5 text-sm font-semibold text-white shadow-lg  transition-all hover: hover:brightness-110 disabled:opacity-50"
            >
              {isLastStep ? "Calculate & Finish" : "Continue"}
            </button>
          </div>
        </FadeSlide>
      </div>
    </div>
  );
}
