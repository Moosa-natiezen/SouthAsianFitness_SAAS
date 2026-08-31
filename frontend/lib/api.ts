export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

/* ── Shared ────────────────────────────────────────────────────────────── */

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers ?? {});

  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const errorPayload = (await response.json()) as {
        detail?: string | Array<{ msg?: string }> | Record<string, unknown>;
      };

      if (typeof errorPayload.detail === "string") {
        message = errorPayload.detail;
      } else if (Array.isArray(errorPayload.detail)) {
        const item = errorPayload.detail[0];
        if (item && typeof item.msg === "string") {
          message = item.msg;
        }
      }
    } catch {
      // Ignore JSON parse failures
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/* ── Auth types ────────────────────────────────────────────────────────── */

export type HealthResponse = {
  status: "ok" | "degraded";
  api: string;
  database: "connected" | "disconnected";
};

export type AuthUser = {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_onboarded: boolean;
};

export type AuthSession = {
  user: AuthUser;
  csrf_token: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type RegisterRequest = {
  email: string;
  password: string;
  display_name: string;
};

export type OnboardingRequest = {
  country_id: string;
  region_id?: string | null;
  preferred_currency_code: string;
  preferred_language: string;
  unit_system: "metric" | "imperial";
  age_years: number;
  sex: "male" | "female" | "other";
  height_cm: number;
  weight_kg: number;
  activity_level:
    | "sedentary"
    | "lightly_active"
    | "moderately_active"
    | "very_active"
    | "extra_active";
  fitness_goal: "weight_loss" | "weight_gain" | "muscle_building" | "general_fitness";
  diet_pattern: "omnivore" | "vegetarian" | "eggetarian" | "vegan" | "pescetarian";
  dietary_tag_slugs: string[];
  allergen_tag_slugs: string[];
  food_dislikes: string[];
  preferred_foods: string[];
  weekly_budget_amount?: number | null;
  budget_period?: string;
};

/* ── Nutrition types ───────────────────────────────────────────────────── */

export type NutritionTargets = {
  calorie_target: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  bmr: number;
  tdee: number;
  goal_adjustment: number;
  is_bounded: boolean;
  warnings: string[];
  sex: string;
  age: number;
  height_cm: number;
  weight_kg: number;
  activity_level: string;
  goal: string;
};

export type BudgetTargets = {
  daily_budget: number | null;
  weekly_budget: number | null;
  monthly_budget: number | null;
  currency_code: string | null;
  country_id: string | null;
  region_id: string | null;
  warnings: string[];
};

export type NutritionBudgetResponse = {
  nutrition: NutritionTargets;
  budget: BudgetTargets;
};

export type FoodEligibilityResponse = {
  eligible_count: number;
  total_count: number;
  eligible_statuses: string[];
};

/* ── Meal plan types ───────────────────────────────────────────────────── */

export type GeneratedFood = {
  food_id: string;
  name: string;
  slug: string;
  serving_quantity: number;
  serving_unit_code: string;
  portion_grams: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  estimated_cost: number | null;
  cost_available: boolean;
};

export type GeneratedMeal = {
  meal_type: string;
  foods: GeneratedFood[];
  subtotal_calories: number;
  subtotal_protein_g: number;
  subtotal_carbs_g: number;
  subtotal_fat_g: number;
  subtotal_estimated_cost: number | null;
  cost_complete: boolean;
};

export type GeneratedDay = {
  plan_date: string;
  meals: GeneratedMeal[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  total_estimated_cost: number | null;
  cost_complete: boolean;
  warnings: string[];
};

export type MealPlanNutrition = {
  calorie_target: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  goal: string;
  is_bounded: boolean;
  warnings: string[];
};

export type MealPlanBudget = {
  daily_budget: number | null;
  weekly_budget: number | null;
  monthly_budget: number | null;
  currency_code: string | null;
};

export type MealPlanResponse = {
  plan_id: string;
  plan_name: string;
  start_date: string;
  end_date: string;
  days: GeneratedDay[];
  nutrition: MealPlanNutrition;
  budget: MealPlanBudget;
  warnings: string[];
};

export type MealPlanFailure = {
  success: false;
  reason: string;
  conflict_details: string[];
  suggestions: string[];
};

export type MealPlanGenerateRequest = {
  plan_days?: number | null;
  meal_count?: number | null;
};

/* ── Locations API ─────────────────────────────────────────────────────── */

export type RegionData = {
  id: string;
  name: string;
  code: string | null;
};

export type CountryData = {
  id: string;
  name: string;
  iso_code: string;
  currency_code: string;
  regions: RegionData[];
};

export async function fetchLocations(): Promise<CountryData[]> {
  return apiFetch<CountryData[]>("/api/locations/");
}

/* ── Auth API ──────────────────────────────────────────────────────────── */

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health");
}

export async function getCsrfToken(): Promise<string> {
  const response = await apiFetch<{ csrf_token: string }>("/api/auth/csrf", {
    method: "GET",
  });
  return response.csrf_token;
}

export async function registerUser(payload: RegisterRequest): Promise<AuthSession> {
  return apiFetch<AuthSession>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: LoginRequest): Promise<AuthSession> {
  return apiFetch<AuthSession>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function logoutUser(): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiFetch<unknown>("/api/auth/logout", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
  });
}

export async function getCurrentUser(): Promise<AuthUser> {
  return apiFetch<AuthUser>("/api/auth/me");
}

export async function submitOnboarding(payload: OnboardingRequest): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiFetch<unknown>("/api/auth/onboarding", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(payload),
  });
}

/* ── Nutrition API ─────────────────────────────────────────────────────── */

export async function getNutritionTargets(): Promise<NutritionTargets> {
  return apiFetch<NutritionTargets>("/api/nutrition/targets");
}

export async function getBudgetTargets(): Promise<BudgetTargets> {
  return apiFetch<BudgetTargets>("/api/nutrition/budget");
}

export async function getNutritionAndBudget(): Promise<NutritionBudgetResponse> {
  return apiFetch<NutritionBudgetResponse>("/api/nutrition/calculate", {
    method: "POST",
  });
}

export async function getEligibleFoods(): Promise<FoodEligibilityResponse> {
  return apiFetch<FoodEligibilityResponse>("/api/nutrition/eligible-foods");
}

/* ── Meal plan API ─────────────────────────────────────────────────────── */

export async function generateMealPlan(
  planDays?: number,
  mealCount?: number,
): Promise<MealPlanResponse | MealPlanFailure> {
  const body: MealPlanGenerateRequest = {};
  if (planDays !== undefined) body.plan_days = planDays;
  if (mealCount !== undefined) body.meal_count = mealCount;

  const csrfToken = await getCsrfToken();
  return apiFetch<MealPlanResponse | MealPlanFailure>("/api/meal-plans/generate", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(body),
  });
}

/* ── Progress API ─────────────────────────────────────────────────────── */

export type ProgressEntry = {
  id: string;
  recorded_on: string;
  weight_kg: number;
  waist_cm: number | null;
  hip_cm: number | null;
  body_fat_percent: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ProgressEntryCreate = {
  recorded_on: string;
  weight_kg: number;
  waist_cm?: number | null;
  hip_cm?: number | null;
  body_fat_percent?: number | null;
  notes?: string | null;
};

export type ProgressSummary = {
  starting_weight_kg: number | null;
  current_weight_kg: number | null;
  weight_change_kg: number | null;
  bmi: number | null;
  fitness_goal: string | null;
  entry_count: number;
  height_cm: number | null;
};

export async function getProgress(): Promise<ProgressEntry[]> {
  return apiFetch<ProgressEntry[]>("/api/progress");
}

export async function createProgressEntry(
  payload: ProgressEntryCreate,
): Promise<ProgressEntry> {
  const csrfToken = await getCsrfToken();
  return apiFetch<ProgressEntry>("/api/progress", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(payload),
  });
}

export async function getProgressSummary(): Promise<ProgressSummary> {
  return apiFetch<ProgressSummary>("/api/progress/summary");
}

export async function deleteProgressEntry(entryId: string): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiFetch<unknown>(`/api/progress/${entryId}`, {
    method: "DELETE",
    headers: { "X-CSRF-Token": csrfToken },
  });
}

/* ── Meal plan API ─────────────────────────────────────────────────────── */

export async function getTodaysMealPlan(): Promise<MealPlanResponse | null> {
  try {
    return await apiFetch<MealPlanResponse>("/api/meal-plans/today");
  } catch (err) {
    const msg = err instanceof Error ? err.message : "";
    // Only treat "no plan found" as a normal 404 — re-throw all other errors
    // so callers can distinguish "no plan" from server/network/auth failures.
    if (msg.includes("No current meal plan found")) {
      return null;
    }
    throw err;
  }
}

/* ── Settings API ─────────────────────────────────────────────────────── */

export type SettingsProfileData = {
  age_years: number | null;
  sex: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  activity_level: string | null;
  fitness_goal: string | null;
  diet_pattern: string | null;
  dietary_tags: string[];
};

export type SettingsPreferencesData = {
  weekly_budget_amount: number | null;
  budget_currency_code: string | null;
  budget_period: string | null;
  dietary_tags: string[];
  cuisine_tags: string[];
  preferred_region_ids: string[];
  food_dislikes: string[];
  preferred_foods: string[];
};

export type SettingsResponse = {
  display_name: string;
  email: string;
  country_id: string | null;
  region_id: string | null;
  preferred_language: string | null;
  preferred_unit_system: string | null;
  preferred_currency_code: string | null;
  profile: SettingsProfileData | null;
  preferences: SettingsPreferencesData | null;
};

export type ProfileUpdatePayload = {
  display_name?: string;
  country_id?: string | null;
  region_id?: string | null;
  preferred_language?: string;
  preferred_unit_system?: string;
  preferred_currency_code?: string;
  age_years?: number;
  sex?: string;
  height_cm?: number;
  weight_kg?: number;
  activity_level?: string;
  fitness_goal?: string;
  diet_pattern?: string;
};

export type PreferencesUpdatePayload = {
  weekly_budget_amount?: number | null;
  budget_currency_code?: string | null;
  budget_period?: string | null;
  dietary_tag_slugs?: string[];
  allergen_tag_slugs?: string[];
  cuisine_tag_slugs?: string[];
  preferred_region_ids?: string[];
  food_dislikes?: string[];
  preferred_foods?: string[];
};

export type ChangePasswordPayload = {
  current_password: string;
  new_password: string;
};

export async function getSettings(): Promise<SettingsResponse> {
  return apiFetch<SettingsResponse>("/api/auth/settings");
}

export async function updateProfile(
  payload: ProfileUpdatePayload,
): Promise<{ status: string }> {
  const csrfToken = await getCsrfToken();
  return apiFetch<{ status: string }>("/api/auth/profile", {
    method: "PATCH",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(payload),
  });
}

export async function updatePreferences(
  payload: PreferencesUpdatePayload,
): Promise<{ status: string }> {
  const csrfToken = await getCsrfToken();
  return apiFetch<{ status: string }>("/api/auth/preferences", {
    method: "PATCH",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(payload),
  });
}

export async function changePassword(
  payload: ChangePasswordPayload,
): Promise<{ status: string }> {
  const csrfToken = await getCsrfToken();
  return apiFetch<{ status: string }>("/api/auth/change-password", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(payload),
  });
}

/* ── Food Library API ────────────────────────────────────────────────── */

export type FoodNutrition = {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number | null;
  sugar_g: number | null;
  sodium_mg: number | null;
};

export type FoodItem = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  category: string | null;
  category_slug: string | null;
  is_active: boolean;
  verification_status: string;
  serving_size: number;
  serving_unit: string;
  grams_per_serving: number | null;
  nutrition: FoodNutrition;
  dietary_tags: string[];
  cuisine_tags: string[];
};

export type FoodListResponse = {
  items: FoodItem[];
  total: number;
  limit: number;
  offset: number;
};

export type FoodCategory = {
  id: string;
  name: string;
  slug: string;
};

export type FoodSearchParams = {
  q?: string;
  category_slug?: string;
  dietary_tag_slug?: string;
  cuisine_tag_slug?: string;
  verification_status?: string;
  limit?: number;
  offset?: number;
};

export async function getFoodCategories(): Promise<FoodCategory[]> {
  return apiFetch<FoodCategory[]>("/api/foods/categories");
}

export async function searchFoods(
  params: FoodSearchParams = {},
): Promise<FoodListResponse> {
  const searchParams = new URLSearchParams();
  if (params.q) searchParams.set("q", params.q);
  if (params.category_slug) searchParams.set("category_slug", params.category_slug);
  if (params.dietary_tag_slug) searchParams.set("dietary_tag_slug", params.dietary_tag_slug);
  if (params.cuisine_tag_slug) searchParams.set("cuisine_tag_slug", params.cuisine_tag_slug);
  if (params.verification_status) searchParams.set("verification_status", params.verification_status);
  if (params.limit) searchParams.set("limit", String(params.limit));
  if (params.offset) searchParams.set("offset", String(params.offset));

  const qs = searchParams.toString();
  const path = `/api/foods${qs ? `?${qs}` : ""}`;
  return apiFetch<FoodListResponse>(path);
}

/* ── Meal Plan Management API ───────────────────────────────────────── */

export type MealPlanSummary = {
  id: string;
  name: string | null;
  start_date: string;
  end_date: string;
  day_count: number;
  status: string;
  calorie_target: number | null;
  created_at: string;
};

export type MealPlanListResponse = {
  items: MealPlanSummary[];
  total: number;
  limit: number;
  offset: number;
};

export async function listMealPlans(
  params: { limit?: number; offset?: number } = {},
): Promise<MealPlanListResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set("limit", String(params.limit));
  if (params.offset) searchParams.set("offset", String(params.offset));
  const qs = searchParams.toString();
  const path = `/api/meal-plans${qs ? `?${qs}` : ""}`;
  return apiFetch<MealPlanListResponse>(path);
}

export async function deleteMealPlan(planId: string): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiFetch<unknown>(`/api/meal-plans/${planId}`, {
    method: "DELETE",
    headers: { "X-CSRF-Token": csrfToken },
  });
}
