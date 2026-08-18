"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { submitOnboarding } from "@/lib/api";

const countryOptions = [
  { value: "11111111-1111-4111-8111-111111111111", label: "Pakistan" },
  { value: "22222222-2222-4222-8222-222222222222", label: "India" },
  { value: "33333333-3333-4333-8333-333333333333", label: "Bangladesh" },
  { value: "44444444-4444-4444-8444-444444444444", label: "Sri Lanka" },
  { value: "55555555-5555-4555-8555-555555555555", label: "Nepal" },
  { value: "66666666-6666-4666-8666-666666666666", label: "United Arab Emirates" },
];

const regionOptions: Record<string, string[]> = {
  "11111111-1111-4111-8111-111111111111": ["Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"],
  "22222222-2222-4222-8222-222222222222": ["Punjab", "Maharashtra", "Karnataka", "West Bengal"],
  "33333333-3333-4333-8333-333333333333": ["Dhaka", "Chittagong", "Khulna", "Sylhet"],
  "44444444-4444-4444-8444-444444444444": ["Western", "Central", "Southern", "Northern"],
  "55555555-5555-4555-8555-555555555555": ["Bagmati", "Lumbini", "Koshi", "Gandaki"],
  "66666666-6666-4666-8666-666666666666": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman"],
};

const steps = [
  { title: "Location", description: "Set your basics and region." },
  { title: "Body info", description: "Add your key measurements." },
  { title: "Goal & activity", description: "Reflect your daily routine and objective." },
  { title: "Food preferences", description: "Tell us what fits your routine." },
  { title: "Budget", description: "Share your realistic food budget." },
];

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
  activity_level: "sedentary" | "light" | "moderate" | "active" | "very_active";
  fitness_goal: "weight_loss" | "weight_gain" | "muscle_building" | "general_fitness";
  dietary_tag_slugs: string;
  allergen_tag_slugs: string;
  food_dislikes: string;
  preferred_foods: string;
  weekly_budget_amount: string;
  budget_period: string;
};

const initialForm: FormState = {
  country_id: "11111111-1111-4111-8111-111111111111",
  region_id: "",
  preferred_currency_code: "PKR",
  preferred_language: "en",
  unit_system: "metric",
  age_years: "28",
  sex: "female",
  height_cm: "165",
  weight_kg: "62",
  activity_level: "moderate",
  fitness_goal: "weight_loss",
  dietary_tag_slugs: "vegetarian,high-protein",
  allergen_tag_slugs: "nuts",
  food_dislikes: "too much fried food",
  preferred_foods: "rice, dal, chicken, yogurt, fruit",
  weekly_budget_amount: "2500",
  budget_period: "weekly",
};

function parseList(values: string) {
  return values
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

export function OnboardingWizard() {
  const router = useRouter();
  const [stepIndex, setStepIndex] = useState(0);
  const [form, setForm] = useState<FormState>(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const currentRegions = regionOptions[form.country_id] ?? [];

  const updateField = <K extends keyof FormState>(field: K, value: FormState[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSelect = (event: ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = event.target;

    if (name === "country_id") {
      setForm((current) => ({
        ...current,
        country_id: value,
        region_id: "",
      }));
      return;
    }

    updateField(name as keyof FormState, value as never);
  };

  const validateStep = () => {
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
      if (!form.dietary_tag_slugs.trim() && !form.preferred_foods.trim()) {
        return "Tell us at least one dietary preference or typical meal.";
      }
      return null;
    }

    if (!form.budget_period.trim()) {
      return "Choose a budget period.";
    }

    return null;
  };

  const canGoBack = stepIndex > 0;
  const isLastStep = stepIndex === steps.length - 1;

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
      const message =
        caughtError instanceof Error ? caughtError.message : "Unable to save onboarding details.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const stepContent = () => {
    if (stepIndex === 0) {
      return (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Country</label>
            <select
              name="country_id"
              value={form.country_id}
              onChange={handleSelect}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            >
              {countryOptions.map((country) => (
                <option key={country.value} value={country.value}>
                  {country.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Region / state / province</label>
            <select
              name="region_id"
              value={form.region_id}
              onChange={(event) => updateField("region_id", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            >
              <option value="">Select region</option>
              {currentRegions.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Preferred currency</label>
            <input
              value={form.preferred_currency_code}
              onChange={(event) => updateField("preferred_currency_code", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
              placeholder="PKR"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Preferred language</label>
            <input
              value={form.preferred_language}
              onChange={(event) => updateField("preferred_language", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
              placeholder="en"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Unit system</label>
            <select
              name="unit_system"
              value={form.unit_system}
              onChange={(event) => updateField("unit_system", event.target.value as FormState["unit_system"])}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            >
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
            <label className="text-sm font-medium text-slate-700">Age</label>
            <input
              type="number"
              min={13}
              max={120}
              value={form.age_years}
              onChange={(event) => updateField("age_years", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Sex</label>
            <select
              name="sex"
              value={form.sex}
              onChange={(event) => updateField("sex", event.target.value as FormState["sex"])}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            >
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Height (cm)</label>
            <input
              type="number"
              value={form.height_cm}
              onChange={(event) => updateField("height_cm", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Weight (kg)</label>
            <input
              type="number"
              value={form.weight_kg}
              onChange={(event) => updateField("weight_kg", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            />
          </div>
        </div>
      );
    }

    if (stepIndex === 2) {
      return (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Activity level</label>
            <select
              name="activity_level"
              value={form.activity_level}
              onChange={(event) => updateField("activity_level", event.target.value as FormState["activity_level"])}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            >
              <option value="sedentary">Sedentary</option>
              <option value="light">Light</option>
              <option value="moderate">Moderate</option>
              <option value="active">Active</option>
              <option value="very_active">Very active</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Primary goal</label>
            <select
              name="fitness_goal"
              value={form.fitness_goal}
              onChange={(event) => updateField("fitness_goal", event.target.value as FormState["fitness_goal"])}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            >
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
            <label className="text-sm font-medium text-slate-700">Dietary preferences</label>
            <input
              value={form.dietary_tag_slugs}
              onChange={(event) => updateField("dietary_tag_slugs", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
              placeholder="vegetarian, high-protein"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Foods liked</label>
            <input
              value={form.preferred_foods}
              onChange={(event) => updateField("preferred_foods", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
              placeholder="rice, dal, chicken, yogurt"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Foods disliked</label>
            <input
              value={form.food_dislikes}
              onChange={(event) => updateField("food_dislikes", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
              placeholder="fried snacks, excessive sugar"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Allergies and restrictions</label>
            <input
              value={form.allergen_tag_slugs}
              onChange={(event) => updateField("allergen_tag_slugs", event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
              placeholder="nuts, dairy"
            />
          </div>
        </div>
      );
    }

    return (
      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Approximate weekly budget</label>
          <input
            type="number"
            min={0}
            value={form.weekly_budget_amount}
            onChange={(event) => updateField("weekly_budget_amount", event.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">Budget frequency</label>
          <select
            name="budget_period"
            value={form.budget_period}
            onChange={(event) => updateField("budget_period", event.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
          >
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="biweekly">Biweekly</option>
          </select>
        </div>
      </div>
    );
  };

  const handleNext = () => {
    const validationError = validateStep();

    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);

    if (isLastStep) {
      void submitForm();
      return;
    }

    setStepIndex((current) => current + 1);
  };

  const handleBack = () => {
    setError(null);
    setStepIndex((current) => Math.max(0, current - 1));
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-8">
      <Card className="w-full max-w-3xl border-slate-200 shadow-xl">
        <CardHeader>
          <CardTitle>Complete your onboarding</CardTitle>
          <CardDescription>{steps[stepIndex].description}</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="flex gap-2">
            {steps.map((step, index) => (
              <div
                key={step.title}
                className={`h-2 flex-1 rounded-full ${
                  index <= stepIndex ? "bg-emerald-600" : "bg-slate-200"
                }`}
              />
            ))}
          </div>

          <div>
            <p className="text-sm font-medium uppercase tracking-[0.12em] text-emerald-700">
              Step {stepIndex + 1} of {steps.length}
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">{steps[stepIndex].title}</h2>
          </div>

          {stepContent()}

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          ) : null}

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
