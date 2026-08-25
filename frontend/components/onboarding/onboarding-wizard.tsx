"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchLocations, submitOnboarding, type CountryData } from "@/lib/api";

/* ── Constants ─────────────────────────────────────────────────────────── */

/** Backend ActivityLevel enum — these exact values are sent to the API. */
const activityLevels = [
  { value: "sedentary", label: "Sedentary", desc: "Desk job, little exercise" },
  { value: "lightly_active", label: "Lightly active", desc: "Light walks, occasional exercise" },
  { value: "moderately_active", label: "Moderately active", desc: "Regular exercise 3–5×/week" },
  { value: "very_active", label: "Very active", desc: "Intense exercise 6–7×/week" },
  { value: "extra_active", label: "Extra active", desc: "Athlete-level training" },
] as const;

/** Backend DietPattern enum values. */
const dietPatterns = [
  { value: "omnivore", label: "Omnivore", desc: "I eat everything" },
  { value: "vegetarian", label: "Vegetarian", desc: "No meat, fish, or poultry" },
  { value: "eggetarian", label: "Eggetarian", desc: "Vegetarian + eggs" },
  { value: "vegan", label: "Vegan", desc: "No animal products" },
  { value: "pescetarian", label: "Pescetarian", desc: "Vegetarian + fish" },
] as const;

const steps = [
  { title: "Location", description: "Set your basics and region." },
  { title: "Body info", description: "Add your key measurements." },
  { title: "Goal & activity", description: "Reflect your daily routine and objective." },
  { title: "Food preferences", description: "Tell us what fits your routine." },
  { title: "Budget", description: "Share your realistic food budget." },
];

/* ── Types ─────────────────────────────────────────────────────────────── */

type FormState = {
  country_id: string;
  region_id: string;
  preferred_currency_code: string;
  preferred_language: string;
  unit_system: "metric" | "imperial";
  age_years: string;
  sex: "female" | "male" | "other";
  height_cm: string;
  weight_kg: string;
  activity_level: "sedentary" | "lightly_active" | "moderately_active" | "very_active" | "extra_active";
  fitness_goal: "weight_loss" | "weight_gain" | "muscle_building" | "general_fitness";
  diet_pattern: "omnivore" | "vegetarian" | "eggetarian" | "vegan" | "pescetarian";
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

/* ── Helpers ───────────────────────────────────────────────────────────── */

function parseList(values: string) {
  return values
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
}

/* ── Component ─────────────────────────────────────────────────────────── */

export function OnboardingWizard() {
  const router = useRouter();
  const [stepIndex, setStepIndex] = useState(0);
  const [form, setForm] = useState<FormState>(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  /* ── Locations data from API ───────────────────────────────────────── */
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
        // Auto-select first country and set its currency
        if (data.length > 0 && !form.country_id) {
          setForm((c) => ({
            ...c,
            country_id: data[0].id,
            preferred_currency_code: data[0].currency_code,
          }));
        }
      } catch (err) {
        if (!cancelled) {
          setLocationsError(
            err instanceof Error ? err.message : "Unable to load countries.",
          );
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
      // When country changes, update currency to match and reset region
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

  /* ── Validation ─────────────────────────────────────────────────────── */

  const validateStep = (): string | null => {
    if (stepIndex === 0) {
      if (!form.country_id) return "Choose a country.";
      if (!form.preferred_currency_code.trim()) return "Add a preferred currency code.";
      return null;
    }
    if (stepIndex === 1) {
      if (!form.age_years || Number(form.age_years) <= 0) return "Enter a valid age.";
      if (!form.sex) return "Select a sex.";
      if (!form.height_cm || Number(form.height_cm) <= 0) return "Enter a valid height.";
      if (!form.weight_kg || Number(form.weight_kg) <= 0) return "Enter a valid weight.";
      return null;
    }
    if (stepIndex === 2) {
      if (!form.activity_level) return "Choose an activity level.";
      if (!form.fitness_goal) return "Select your primary goal.";
      return null;
    }
    if (stepIndex === 3) {
      if (!form.diet_pattern) return "Select your diet pattern.";
      return null;
    }
    if (!form.budget_period.trim()) return "Choose a budget period.";
    return null;
  };

  /* ── Navigation ─────────────────────────────────────────────────────── */

  const canGoBack = stepIndex > 0;
  const isLastStep = stepIndex === steps.length - 1;

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

  /* ── Submit ─────────────────────────────────────────────────────────── */

  const submitForm = async () => {
    setError(null);
    setLoading(true);
    try {
      await submitOnboarding({
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
      router.push("/dashboard");
      router.refresh();
    } catch (caughtError) {
      setError(
        caughtError instanceof Error ? caughtError.message : "Unable to save onboarding details.",
      );
    } finally {
      setLoading(false);
    }
  };

  /* ── Step content ───────────────────────────────────────────────────── */

  const renderStep = () => {
    const selectClass =
      "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100";
    const inputClass = selectClass;

    if (stepIndex === 0) {
      if (locationsLoading) {
        return (
          <div className="flex items-center justify-center py-8" aria-live="polite">
            <p className="text-sm text-slate-500">Loading countries...</p>
          </div>
        );
      }
      if (locationsError) {
        return (
          <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {locationsError}
          </div>
        );
      }
      return (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="country" className="text-sm font-medium text-slate-700">Country</label>
            <select id="country" name="country_id" value={form.country_id} onChange={handleSelect} className={selectClass}>
              {countries.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
            </select>
          </div>
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="region" className="text-sm font-medium text-slate-700">Region / state / province</label>
            <select id="region" name="region_id" value={form.region_id} onChange={(e) => updateField("region_id", e.target.value)} className={selectClass}>
              <option value="">Select region</option>
              {currentRegions.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
            </select>
          </div>
          <div className="space-y-2">
            <label htmlFor="currency" className="text-sm font-medium text-slate-700">Preferred currency</label>
            <input id="currency" value={form.preferred_currency_code} onChange={(e) => updateField("preferred_currency_code", e.target.value)} className={inputClass} placeholder="PKR" />
          </div>
          <div className="space-y-2">
            <label htmlFor="language" className="text-sm font-medium text-slate-700">Preferred language</label>
            <input id="language" value={form.preferred_language} onChange={(e) => updateField("preferred_language", e.target.value)} className={inputClass} placeholder="en" />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="unit_system" className="text-sm font-medium text-slate-700">Unit system</label>
            <select id="unit_system" name="unit_system" value={form.unit_system} onChange={(e) => updateField("unit_system", e.target.value as FormState["unit_system"])} className={selectClass}>
              <option value="metric">Metric</option>
              <option value="imperial">Imperial</option>
            </select>
          </div>
        </div>
      );
    }

    if (stepIndex === 1) {
      return (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="space-y-2">
            <label htmlFor="age" className="text-sm font-medium text-slate-700">Age</label>
            <input id="age" type="number" min={13} max={120} value={form.age_years} onChange={(e) => updateField("age_years", e.target.value)} className={inputClass} />
          </div>
          <div className="space-y-2">
            <label htmlFor="sex" className="text-sm font-medium text-slate-700">Sex</label>
            <select id="sex" name="sex" value={form.sex} onChange={(e) => updateField("sex", e.target.value as FormState["sex"])} className={selectClass}>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="space-y-2">
            <label htmlFor="height" className="text-sm font-medium text-slate-700">Height (cm)</label>
            <input id="height" type="number" value={form.height_cm} onChange={(e) => updateField("height_cm", e.target.value)} className={inputClass} />
          </div>
          <div className="space-y-2">
            <label htmlFor="weight" className="text-sm font-medium text-slate-700">Weight (kg)</label>
            <input id="weight" type="number" value={form.weight_kg} onChange={(e) => updateField("weight_kg", e.target.value)} className={inputClass} />
          </div>
        </div>
      );
    }

    if (stepIndex === 2) {
      return (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="space-y-2">
            <label htmlFor="activity" className="text-sm font-medium text-slate-700">Activity level</label>
            <select id="activity" name="activity_level" value={form.activity_level} onChange={(e) => updateField("activity_level", e.target.value as FormState["activity_level"])} className={selectClass}>
              {activityLevels.map((a) => (<option key={a.value} value={a.value}>{a.label} — {a.desc}</option>))}
            </select>
          </div>
          <div className="space-y-2">
            <label htmlFor="goal" className="text-sm font-medium text-slate-700">Primary goal</label>
            <select id="goal" name="fitness_goal" value={form.fitness_goal} onChange={(e) => updateField("fitness_goal", e.target.value as FormState["fitness_goal"])} className={selectClass}>
              <option value="weight_loss">Weight loss</option>
              <option value="weight_gain">Weight gain</option>
              <option value="muscle_building">Muscle building</option>
              <option value="general_fitness">General fitness</option>
            </select>
          </div>
        </div>
      );
    }

    if (stepIndex === 3) {
      return (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="diet_pattern" className="text-sm font-medium text-slate-700">Diet pattern</label>
            <select id="diet_pattern" name="diet_pattern" value={form.diet_pattern} onChange={(e) => updateField("diet_pattern", e.target.value as FormState["diet_pattern"])} className={selectClass}>
              {dietPatterns.map((d) => (<option key={d.value} value={d.value}>{d.label} — {d.desc}</option>))}
            </select>
          </div>
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="preferred_foods" className="text-sm font-medium text-slate-700">Foods you like (optional)</label>
            <input id="preferred_foods" value={form.preferred_foods} onChange={(e) => updateField("preferred_foods", e.target.value)} className={inputClass} placeholder="rice, dal, chicken, yogurt" />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="food_dislikes" className="text-sm font-medium text-slate-700">Foods you dislike (optional)</label>
            <input id="food_dislikes" value={form.food_dislikes} onChange={(e) => updateField("food_dislikes", e.target.value)} className={inputClass} placeholder="fried snacks, excessive sugar" />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label htmlFor="allergies" className="text-sm font-medium text-slate-700">Allergies / restrictions (optional)</label>
            <input id="allergies" value={form.allergen_tag_slugs} onChange={(e) => updateField("allergen_tag_slugs", e.target.value)} className={inputClass} placeholder="nuts, dairy" />
          </div>
        </div>
      );
    }

    // Step 5: Budget
    return (
      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="budget" className="text-sm font-medium text-slate-700">Approximate weekly budget</label>
          <input id="budget" type="number" min={0} value={form.weekly_budget_amount} onChange={(e) => updateField("weekly_budget_amount", e.target.value)} className={inputClass} placeholder="2500" />
        </div>
        <div className="space-y-2">
          <label htmlFor="budget_period" className="text-sm font-medium text-slate-700">Budget frequency</label>
          <select id="budget_period" name="budget_period" value={form.budget_period} onChange={(e) => updateField("budget_period", e.target.value)} className={selectClass}>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
      </div>
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-8">
      <Card className="w-full max-w-3xl border-slate-200 shadow-xl">
        <CardHeader>
          <CardTitle>Complete your onboarding</CardTitle>
          <CardDescription>{steps[stepIndex].description}</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Progress bar */}
          <div className="flex gap-2" role="progressbar" aria-valuenow={stepIndex + 1} aria-valuemax={steps.length} aria-label={`Step ${stepIndex + 1} of ${steps.length}`}>
            {steps.map((step, index) => (
              <div key={step.title} className={`h-2 flex-1 rounded-full transition-colors ${index <= stepIndex ? "bg-emerald-600" : "bg-slate-200"}`} />
            ))}
          </div>

          <div>
            <p className="text-sm font-medium uppercase tracking-[0.12em] text-emerald-700">
              Step {stepIndex + 1} of {steps.length}
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">{steps[stepIndex].title}</h2>
          </div>

          {renderStep()}

          {error && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex justify-between gap-3 pt-2">
            <Button variant="outline" onClick={handleBack} disabled={!canGoBack || loading}>
              Back
            </Button>
            <Button onClick={handleNext} disabled={loading}>
              {loading ? "Saving..." : isLastStep ? "Finish onboarding" : "Next"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
