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
