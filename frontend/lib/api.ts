export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

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
  is_verified: boolean;
  is_onboarded: boolean;
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
  activity_level: "sedentary" | "light" | "moderate" | "active" | "very_active";
  fitness_goal: "weight_loss" | "weight_gain" | "muscle_building" | "general_fitness";
  dietary_tag_slugs: string[];
  allergen_tag_slugs: string[];
  food_dislikes: string[];
  preferred_foods: string[];
  weekly_budget_amount?: number | null;
  budget_period?: string;
};

export type AuthSession = {
  user: AuthUser;
  csrf_token: string;
};

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
      // Ignore JSON parse failures and keep the default error message.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health");
}

export async function getCsrfToken(): Promise<string> {
  const response = await apiFetch<{ csrf_token: string }>("/auth/csrf", {
    method: "GET",
  });

  return response.csrf_token;
}

export async function registerUser(payload: RegisterRequest): Promise<AuthSession> {
  return apiFetch<AuthSession>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: LoginRequest): Promise<AuthSession> {
  return apiFetch<AuthSession>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function logoutUser(): Promise<void> {
  const csrfToken = await getCsrfToken();

  await apiFetch<unknown>("/auth/logout", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
  });
}

export async function getCurrentUser(): Promise<AuthUser> {
  return apiFetch<AuthUser>("/auth/me");
}

export async function submitOnboarding(payload: OnboardingRequest): Promise<void> {
  const csrfToken = await getCsrfToken();

  await apiFetch<unknown>("/auth/onboarding", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    body: JSON.stringify(payload),
  });
}
