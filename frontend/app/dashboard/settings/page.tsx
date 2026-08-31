"use client";

import { useEffect, useState } from "react";

import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  createCheckoutSession,
  createPortalSession,
  fetchLocations,
  getCurrentUser,
  getSettings,
  updateProfile,
  updatePreferences,
  changePassword,
  type AuthUser,
  type CountryData,
  type SettingsResponse,
} from "@/lib/api";

/* ── Constants ─────────────────────────────────────────────────────────── */

const activityLevels = [
  { value: "sedentary", label: "Sedentary" },
  { value: "lightly_active", label: "Lightly active" },
  { value: "moderately_active", label: "Moderately active" },
  { value: "very_active", label: "Very active" },
  { value: "extra_active", label: "Extra active" },
] as const;

const fitnessGoals = [
  { value: "weight_loss", label: "Weight loss" },
  { value: "weight_gain", label: "Weight gain" },
  { value: "muscle_building", label: "Muscle building" },
  { value: "general_fitness", label: "General fitness" },
] as const;

const dietPatterns = [
  { value: "omnivore", label: "Omnivore" },
  { value: "vegetarian", label: "Vegetarian" },
  { value: "eggetarian", label: "Eggetarian" },
  { value: "vegan", label: "Vegan" },
  { value: "pescetarian", label: "Pescetarian" },
] as const;

const unitSystems = [
  { value: "metric", label: "Metric" },
  { value: "imperial", label: "Imperial" },
] as const;

const sexOptions = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
] as const;

const budgetPeriods = [
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
] as const;

/* ── Shared styles ─────────────────────────────────────────────────────── */

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 text-sm";

const labelClass = "text-sm font-medium text-slate-700";

/* ── Component ─────────────────────────────────────────────────────────── */

export default function SettingsPage() {
  /* ── Data state ──────────────────────────────────────────────────── */
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [countries, setCountries] = useState<CountryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* ── Profile form ────────────────────────────────────────────────── */
  const [displayName, setDisplayName] = useState("");
  const [ageYears, setAgeYears] = useState("");
  const [sex, setSex] = useState("male");
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [activityLevel, setActivityLevel] = useState("moderately_active");
  const [fitnessGoal, setFitnessGoal] = useState("weight_loss");
  const [dietPattern, setDietPattern] = useState("omnivore");
  const [countryId, setCountryId] = useState("");
  const [regionId, setRegionId] = useState("");
  const [currencyCode, setCurrencyCode] = useState("");
  const [unitSystem, setUnitSystem] = useState("metric");
  const [preferredLanguage, setPreferredLanguage] = useState("en");

  /* ── Preferences form ────────────────────────────────────────────── */
  const [foodDislikes, setFoodDislikes] = useState("");
  const [preferredFoods, setPreferredFoods] = useState("");
  const [allergenTags, setAllergenTags] = useState("");
  const [dietaryTags, setDietaryTags] = useState("");
  const [cuisineTags, setCuisineTags] = useState("");
  const [weeklyBudget, setWeeklyBudget] = useState("");
  const [budgetPeriod, setBudgetPeriod] = useState("weekly");

  /* ── Billing state ────────────────────────────────────────────────── */
  const [user, setUser] = useState<AuthUser | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const [billingMsg, setBillingMsg] = useState<{
    type: "info" | "error";
    text: string;
  } | null>(null);

  /* ── Password form ───────────────────────────────────────────────── */
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  /* ── UI state ────────────────────────────────────────────────────── */
  const [profileSaving, setProfileSaving] = useState(false);
  const [prefsSaving, setPrefsSaving] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{
    type: "info" | "warning" | "error";
    text: string;
  } | null>(null);
  const [prefsMsg, setPrefsMsg] = useState<{
    type: "info" | "warning" | "error";
    text: string;
  } | null>(null);
  const [passwordMsg, setPasswordMsg] = useState<{
    type: "info" | "warning" | "error";
    text: string;
  } | null>(null);

  /* ── Derived ─────────────────────────────────────────────────────── */

  const selectedCountry = countries.find((c) => c.id === countryId);
  const currentRegions = selectedCountry?.regions ?? [];

  /* ── Load data ───────────────────────────────────────────────────── */

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [settingsData, locationsData, userData] = await Promise.all([
          getSettings(),
          fetchLocations(),
          getCurrentUser(),
        ]);
        if (cancelled) return;

        setSettings(settingsData);
        setCountries(locationsData);
        setUser(userData);

        // Populate profile form
        setDisplayName(settingsData.display_name ?? "");
        setCountryId(settingsData.country_id ?? "");
        setRegionId(settingsData.region_id ?? "");
        setCurrencyCode(settingsData.preferred_currency_code ?? "PKR");
        setUnitSystem(settingsData.preferred_unit_system ?? "metric");
        setPreferredLanguage(settingsData.preferred_language ?? "en");

        if (settingsData.profile) {
          const p = settingsData.profile;
          setAgeYears(p.age_years?.toString() ?? "");
          setSex(p.sex ?? "male");
          setHeightCm(p.height_cm?.toString() ?? "");
          setWeightKg(p.weight_kg?.toString() ?? "");
          setActivityLevel(p.activity_level ?? "moderately_active");
          setFitnessGoal(p.fitness_goal ?? "weight_loss");
          setDietPattern(p.diet_pattern ?? "omnivore");
          setDietaryTags((p.dietary_tags ?? []).join(", "));
        }

        if (settingsData.preferences) {
          const pr = settingsData.preferences;
          setFoodDislikes((pr.food_dislikes ?? []).join(", "));
          setPreferredFoods((pr.preferred_foods ?? []).join(", "));
          setAllergenTags(
            (pr.dietary_tags ?? []).filter((t) => !pr.food_dislikes?.includes(t)).join(", "),
          );
          setCuisineTags((pr.cuisine_tags ?? []).join(", "));
          setWeeklyBudget(pr.weekly_budget_amount?.toString() ?? "");
          setBudgetPeriod(pr.budget_period ?? "weekly");
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Unable to load settings.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Handlers ─────────────────────────────────────────────────────── */

  const handleCountryChange = (newCountryId: string) => {
    setCountryId(newCountryId);
    const newCountry = countries.find((c) => c.id === newCountryId);
    if (newCountry) {
      setCurrencyCode(newCountry.currency_code);
    }
    setRegionId("");
  };

  const handleSaveProfile = async () => {
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      await updateProfile({
        display_name: displayName.trim(),
        country_id: countryId || undefined,
        region_id: regionId || null,
        preferred_currency_code: currencyCode.toUpperCase() || undefined,
        preferred_language: preferredLanguage || undefined,
        preferred_unit_system: unitSystem || undefined,
        age_years: ageYears ? Number(ageYears) : undefined,
        sex: sex || undefined,
        height_cm: heightCm ? Number(heightCm) : undefined,
        weight_kg: weightKg ? Number(weightKg) : undefined,
        activity_level: activityLevel || undefined,
        fitness_goal: fitnessGoal || undefined,
        diet_pattern: dietPattern || undefined,
      });
      setProfileMsg({ type: "info", text: "Profile saved successfully." });
    } catch (err) {
      setProfileMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to save profile.",
      });
    } finally {
      setProfileSaving(false);
    }
  };

  const handleSavePreferences = async () => {
    setPrefsSaving(true);
    setPrefsMsg(null);
    try {
      const parseList = (s: string) =>
        s
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean);

      await updatePreferences({
        weekly_budget_amount: weeklyBudget ? Number(weeklyBudget) : null,
        budget_period: budgetPeriod || undefined,
        food_dislikes: parseList(foodDislikes),
        preferred_foods: parseList(preferredFoods),
        dietary_tag_slugs: parseList(dietaryTags),
        allergen_tag_slugs: parseList(allergenTags),
        cuisine_tag_slugs: parseList(cuisineTags),
      });
      setPrefsMsg({ type: "info", text: "Preferences saved successfully." });
    } catch (err) {
      setPrefsMsg({
        type: "error",
        text:
          err instanceof Error ? err.message : "Failed to save preferences.",
      });
    } finally {
      setPrefsSaving(false);
    }
  };

  const handleManageBilling = async () => {
    setPortalLoading(true);
    setBillingMsg(null);
    try {
      // Free users → checkout page; Pro users → customer portal
      if (user?.subscription_tier === "pro") {
        const result = await createPortalSession();
        if (result.portal_url) {
          window.location.href = result.portal_url;
        } else {
          setBillingMsg({ type: "error", text: "No billing portal available for your account." });
          setPortalLoading(false);
        }
      } else {
        const result = await createCheckoutSession();
        window.location.href = result.checkout_url;
      }
    } catch (err) {
      setBillingMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to open billing.",
      });
      setPortalLoading(false);
    }
  };

  const handleChangePassword = async () => {
    setPasswordMsg(null);
    if (!currentPassword || !newPassword) {
      setPasswordMsg({ type: "warning", text: "Please fill in all password fields." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: "warning", text: "New passwords do not match." });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMsg({
        type: "warning",
        text: "New password must be at least 8 characters.",
      });
      return;
    }
    setPasswordSaving(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMsg({ type: "info", text: "Password updated successfully." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPasswordMsg({
        type: "error",
        text: err instanceof Error ? err.message : "Failed to change password.",
      });
    } finally {
      setPasswordSaving(false);
    }
  };

  /* ── Loading state ───────────────────────────────────────────────── */

  if (loading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold text-slate-900">Settings</h2>
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold text-slate-900">Settings</h2>
        <AlertBanner variant="error" message={error} />
      </div>
    );
  }

  /* ── Render ──────────────────────────────────────────────────────── */

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-slate-900">Settings</h2>

      {/* ── Profile & Location Card ──────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <CardDescription>
            Update your display name, body measurements, activity level, and
            location.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {profileMsg && (
            <AlertBanner variant={profileMsg.type} message={profileMsg.text} />
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {/* Display name */}
            <div className="space-y-1 md:col-span-2">
              <label htmlFor="display_name" className={labelClass}>
                Display name
              </label>
              <input
                id="display_name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className={inputClass}
                placeholder="Your name"
              />
            </div>

            {/* Age */}
            <div className="space-y-1">
              <label htmlFor="age" className={labelClass}>
                Age
              </label>
              <input
                id="age"
                type="number"
                min={13}
                max={120}
                value={ageYears}
                onChange={(e) => setAgeYears(e.target.value)}
                className={inputClass}
              />
            </div>

            {/* Sex */}
            <div className="space-y-1">
              <label htmlFor="sex" className={labelClass}>
                Sex
              </label>
              <select
                id="sex"
                value={sex}
                onChange={(e) => setSex(e.target.value)}
                className={inputClass}
              >
                {sexOptions.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Height */}
            <div className="space-y-1">
              <label htmlFor="height" className={labelClass}>
                Height (cm)
              </label>
              <input
                id="height"
                type="number"
                value={heightCm}
                onChange={(e) => setHeightCm(e.target.value)}
                className={inputClass}
              />
            </div>

            {/* Weight */}
            <div className="space-y-1">
              <label htmlFor="weight" className={labelClass}>
                Weight (kg)
              </label>
              <input
                id="weight"
                type="number"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                className={inputClass}
              />
            </div>

            {/* Activity level */}
            <div className="space-y-1">
              <label htmlFor="activity" className={labelClass}>
                Activity level
              </label>
              <select
                id="activity"
                value={activityLevel}
                onChange={(e) => setActivityLevel(e.target.value)}
                className={inputClass}
              >
                {activityLevels.map((a) => (
                  <option key={a.value} value={a.value}>
                    {a.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Fitness goal */}
            <div className="space-y-1">
              <label htmlFor="goal" className={labelClass}>
                Fitness goal
              </label>
              <select
                id="goal"
                value={fitnessGoal}
                onChange={(e) => setFitnessGoal(e.target.value)}
                className={inputClass}
              >
                {fitnessGoals.map((g) => (
                  <option key={g.value} value={g.value}>
                    {g.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Diet pattern */}
            <div className="space-y-1">
              <label htmlFor="diet" className={labelClass}>
                Diet pattern
              </label>
              <select
                id="diet"
                value={dietPattern}
                onChange={(e) => setDietPattern(e.target.value)}
                className={inputClass}
              >
                {dietPatterns.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Country */}
            <div className="space-y-1 md:col-span-2">
              <label htmlFor="country" className={labelClass}>
                Country
              </label>
              <select
                id="country"
                value={countryId}
                onChange={(e) => handleCountryChange(e.target.value)}
                className={inputClass}
              >
                <option value="">Select country</option>
                {countries.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Region */}
            <div className="space-y-1 md:col-span-2">
              <label htmlFor="region" className={labelClass}>
                Region / state / province
              </label>
              <select
                id="region"
                value={regionId}
                onChange={(e) => setRegionId(e.target.value)}
                className={inputClass}
              >
                <option value="">Select region</option>
                {currentRegions.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Currency */}
            <div className="space-y-1">
              <label htmlFor="currency" className={labelClass}>
                Preferred currency
              </label>
              <input
                id="currency"
                value={currencyCode}
                onChange={(e) => setCurrencyCode(e.target.value)}
                className={inputClass}
                placeholder="PKR"
              />
            </div>

            {/* Unit system */}
            <div className="space-y-1">
              <label htmlFor="unit" className={labelClass}>
                Unit system
              </label>
              <select
                id="unit"
                value={unitSystem}
                onChange={(e) => setUnitSystem(e.target.value)}
                className={inputClass}
              >
                {unitSystems.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Language */}
            <div className="space-y-1">
              <label htmlFor="language" className={labelClass}>
                Preferred language
              </label>
              <input
                id="language"
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                className={inputClass}
                placeholder="en"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button onClick={handleSaveProfile} disabled={profileSaving}>
              {profileSaving ? "Saving..." : "Save Profile"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Dietary Preferences Card ─────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Dietary Preferences</CardTitle>
          <CardDescription>
            Manage your diet pattern, allergies, and food preferences.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {prefsMsg && (
            <AlertBanner variant={prefsMsg.type} message={prefsMsg.text} />
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1 md:col-span-2">
              <label htmlFor="pref_diet" className={labelClass}>
                Diet pattern
              </label>
              <select
                id="pref_diet"
                value={dietPattern}
                onChange={(e) => setDietPattern(e.target.value)}
                className={inputClass}
              >
                {dietPatterns.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1 md:col-span-2">
              <label htmlFor="allergies" className={labelClass}>
                Allergies / restrictions (comma-separated)
              </label>
              <input
                id="allergies"
                value={allergenTags}
                onChange={(e) => setAllergenTags(e.target.value)}
                className={inputClass}
                placeholder="nuts, dairy, gluten"
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label htmlFor="dietary" className={labelClass}>
                Dietary tags (comma-separated)
              </label>
              <input
                id="dietary"
                value={dietaryTags}
                onChange={(e) => setDietaryTags(e.target.value)}
                className={inputClass}
                placeholder="low_carb, high_protein"
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label htmlFor="pref_foods" className={labelClass}>
                Preferred foods (comma-separated)
              </label>
              <input
                id="pref_foods"
                value={preferredFoods}
                onChange={(e) => setPreferredFoods(e.target.value)}
                className={inputClass}
                placeholder="rice, dal, chicken, yogurt"
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label htmlFor="disliked" className={labelClass}>
                Foods you dislike (comma-separated)
              </label>
              <input
                id="disliked"
                value={foodDislikes}
                onChange={(e) => setFoodDislikes(e.target.value)}
                className={inputClass}
                placeholder="bitter_gourd, fried_snacks"
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label htmlFor="cuisines" className={labelClass}>
                Cuisine preferences (comma-separated)
              </label>
              <input
                id="cuisines"
                value={cuisineTags}
                onChange={(e) => setCuisineTags(e.target.value)}
                className={inputClass}
                placeholder="pakistani, indian, chinese"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button onClick={handleSavePreferences} disabled={prefsSaving}>
              {prefsSaving ? "Saving..." : "Save Preferences"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Budget Card ──────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Budget</CardTitle>
          <CardDescription>
            Set your weekly or monthly food budget.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1">
              <label htmlFor="budget" className={labelClass}>
                Budget amount
              </label>
              <input
                id="budget"
                type="number"
                min={0}
                value={weeklyBudget}
                onChange={(e) => setWeeklyBudget(e.target.value)}
                className={inputClass}
                placeholder="2500"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="budget_period" className={labelClass}>
                Budget frequency
              </label>
              <select
                id="budget_period"
                value={budgetPeriod}
                onChange={(e) => setBudgetPeriod(e.target.value)}
                className={inputClass}
              >
                {budgetPeriods.map((bp) => (
                  <option key={bp.value} value={bp.value}>
                    {bp.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button onClick={handleSavePreferences} disabled={prefsSaving}>
              {prefsSaving ? "Saving..." : "Save Budget"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Security Card ────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription>Change your account password.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {passwordMsg && (
            <AlertBanner
              variant={passwordMsg.type}
              message={passwordMsg.text}
            />
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1">
              <label htmlFor="current_pw" className={labelClass}>
                Current password
              </label>
              <input
                id="current_pw"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className={inputClass}
                autoComplete="current-password"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="new_pw" className={labelClass}>
                New password
              </label>
              <input
                id="new_pw"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={inputClass}
                autoComplete="new-password"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="confirm_pw" className={labelClass}>
                Confirm new password
              </label>
              <input
                id="confirm_pw"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={inputClass}
                autoComplete="new-password"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button onClick={handleChangePassword} disabled={passwordSaving}>
              {passwordSaving ? "Updating..." : "Update Password"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Billing Card ──────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Billing & Subscription</CardTitle>
          <CardDescription>
            Manage your subscription and billing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {billingMsg && (
            <AlertBanner variant={billingMsg.type} message={billingMsg.text} />
          )}

          <div className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-slate-700">Current Plan</p>
              <p className="text-lg font-semibold text-slate-900">
                {user?.subscription_tier === "pro" ? "Pro" : "Free"}
              </p>
            </div>
            {user?.subscription_tier !== "pro" && (
              <Button onClick={handleManageBilling} disabled={portalLoading}>
                {portalLoading ? "Loading..." : "Upgrade to Pro"}
              </Button>
            )}
          </div>

          {user?.subscription_tier === "pro" && (
            <div className="flex justify-end">
              <Button variant="outline" onClick={handleManageBilling} disabled={portalLoading}>
                {portalLoading ? "Loading..." : "Manage Billing"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
