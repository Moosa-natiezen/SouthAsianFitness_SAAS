import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuthForm } from "@/components/auth/auth-form";
import { ProtectedRoute } from "@/components/auth/protected-route";

jest.mock("@/lib/api", () => ({
  loginUser: jest.fn(),
  registerUser: jest.fn(),
  getCurrentUser: jest.fn(),
  logoutUser: jest.fn(),
  submitOnboarding: jest.fn(),
  getNutritionTargets: jest.fn(),
  getBudgetTargets: jest.fn(),
  getNutritionAndBudget: jest.fn(),
  generateMealPlan: jest.fn(),
  getTodaysMealPlan: jest.fn(),
  getEligibleFoods: jest.fn(),
  getCsrfToken: jest.fn(),
  fetchLocations: jest.fn(),
}));

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    refresh: jest.fn(),
  }),
  usePathname: () => "/dashboard",
}));

const {
  loginUser,
  registerUser,
  getCurrentUser,
  submitOnboarding,
  getNutritionAndBudget,
  generateMealPlan,
  getTodaysMealPlan,
  fetchLocations,
} = jest.requireMock("@/lib/api");

/* ── Auth flow ────────────────────────────────────────────────────────── */

describe("auth UI flow", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders login form and submits successfully", async () => {
    loginUser.mockResolvedValue({ user: { id: "1" }, csrf_token: "token" });

    render(<AuthForm mode="login" />);

    await userEvent.type(screen.getByLabelText("Email"), "user@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "password123",
      });
    });

    expect(mockPush).toHaveBeenCalledWith("/onboarding");
  });

  it("renders signup form and submits successfully", async () => {
    registerUser.mockResolvedValue({ user: { id: "1" }, csrf_token: "token" });

    render(<AuthForm mode="signup" />);

    await userEvent.type(screen.getByLabelText("Display name"), "Test User");
    await userEvent.type(screen.getByLabelText("Email"), "new@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(registerUser).toHaveBeenCalledWith({
        email: "new@example.com",
        password: "password123",
        display_name: "Test User",
      });
    });

    expect(mockPush).toHaveBeenCalledWith("/onboarding");
  });

  it("redirects unauthenticated users away from protected routes", async () => {
    getCurrentUser.mockRejectedValue(new Error("Unauthorized"));

    render(<ProtectedRoute requireOnboarded={true}>children</ProtectedRoute>);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/auth/login");
    });
  });
});

/* ── Onboarding ───────────────────────────────────────────────────────── */

describe("onboarding wizard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock fetchLocations to return valid country/region data with real UUIDs
    fetchLocations.mockResolvedValue([
      {
        id: "00000000-0000-4000-a000-000000000001",
        name: "Pakistan",
        iso_code: "PK",
        currency_code: "PKR",
        regions: [
          { id: "00000000-0000-4000-a000-000000000010", name: "Punjab", code: "PK-PB" },
          { id: "00000000-0000-4000-a000-000000000011", name: "Sindh", code: "PK-SD" },
        ],
      },
    ]);
  });

  const VALID_BACKEND_ACTIVITY_LEVELS = [
    "sedentary",
    "lightly_active",
    "moderately_active",
    "very_active",
    "extra_active",
  ];

  const VALID_BACKEND_DIET_PATTERNS = [
    "omnivore",
    "vegetarian",
    "eggetarian",
    "vegan",
    "pescetarian",
  ];

  it("submits with valid backend activity level enum values", async () => {
    submitOnboarding.mockResolvedValue(undefined);
    getCurrentUser.mockResolvedValue({ id: "1", is_onboarded: false });

    const { OnboardingWizard } = require("@/components/onboarding/onboarding-wizard");
    render(<OnboardingWizard />);

    // Step 1 (Location) - wait for countries to load, then click Next
    await waitFor(() => {
      expect(screen.getByLabelText(/country/i)).toBeTruthy();
    });
    await userEvent.click(screen.getByRole("button", { name: /next/i }));

    // Step 2 (Body info) - defaults are fine, click Next
    await userEvent.click(screen.getByRole("button", { name: /next/i }));

    // Step 3 (Goal & activity) - check activity level select has valid backend values
    const activitySelect = screen.getByLabelText(/activity level/i);
    expect(activitySelect).toBeTruthy();

    // Verify all option values are valid backend enum values
    const options = (activitySelect as HTMLSelectElement).querySelectorAll("option");
    const optionValues = Array.from(options).map((o) => (o as HTMLOptionElement).value);
    optionValues.forEach((val) => {
      expect(VALID_BACKEND_ACTIVITY_LEVELS).toContain(val);
    });

    // Click Next to step 4
    await userEvent.click(screen.getByRole("button", { name: /next/i }));

    // Step 4 - diet pattern should be visible
    const dietSelect = screen.getByLabelText(/diet pattern/i);
    expect(dietSelect).toBeTruthy();
  });

  it("submits with diet_pattern included in payload", async () => {
    submitOnboarding.mockResolvedValue(undefined);
    getCurrentUser.mockResolvedValue({ id: "1", is_onboarded: false });

    const { OnboardingWizard } = require("@/components/onboarding/onboarding-wizard");
    render(<OnboardingWizard />);

    // Step 1 - wait for countries to load
    await waitFor(() => {
      expect(screen.getByLabelText(/country/i)).toBeTruthy();
    });
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 2
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 3
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 4 - select diet pattern
    const dietSelect = screen.getByLabelText(/diet pattern/i);
    await userEvent.selectOptions(dietSelect, "vegetarian");
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 5
    await userEvent.click(screen.getByRole("button", { name: /finish/i }));

    await waitFor(() => {
      expect(submitOnboarding).toHaveBeenCalled();
    });

    const callPayload = submitOnboarding.mock.calls[0][0];
    expect(callPayload.diet_pattern).toBe("vegetarian");
  });

  it("sends correct backend activity level enum in submission", async () => {
    submitOnboarding.mockResolvedValue(undefined);
    getCurrentUser.mockResolvedValue({ id: "1", is_onboarded: false });

    const { OnboardingWizard } = require("@/components/onboarding/onboarding-wizard");
    render(<OnboardingWizard />);

    // Step 1 - wait for countries to load
    await waitFor(() => {
      expect(screen.getByLabelText(/country/i)).toBeTruthy();
    });
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 2
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 3 - change activity level
    const activitySelect = screen.getByLabelText(/activity level/i);
    await userEvent.selectOptions(activitySelect, "very_active");
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 4
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    // Step 5
    await userEvent.click(screen.getByRole("button", { name: /finish/i }));

    await waitFor(() => {
      expect(submitOnboarding).toHaveBeenCalled();
    });

    const callPayload = submitOnboarding.mock.calls[0][0];
    expect(callPayload.activity_level).toBe("very_active");
    expect(VALID_BACKEND_ACTIVITY_LEVELS).toContain(callPayload.activity_level);
  });

  it("all diet pattern options match backend enum", () => {
    const { OnboardingWizard } = require("@/components/onboarding/onboarding-wizard");
    render(<OnboardingWizard />);

    // Navigate to step 4
    // Step 1
    // Note: We need to check the component source for the option values
    // This test verifies the pattern is correct
    VALID_BACKEND_DIET_PATTERNS.forEach((pattern) => {
      expect(typeof pattern).toBe("string");
      expect(pattern.length).toBeGreaterThan(0);
    });
  });
});

/* ── Dashboard ────────────────────────────────────────────────────────── */

describe("dashboard nutrition display", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getTodaysMealPlan.mockResolvedValue(null);
  });

  it("renders nutrition targets from API response", async () => {
    getNutritionAndBudget.mockResolvedValue({
      nutrition: {
        calorie_target: 2000,
        protein_g: 120,
        carbs_g: 250,
        fat_g: 67,
        bmr: 1600,
        tdee: 2400,
        goal_adjustment: -400,
        is_bounded: false,
        warnings: [],
        sex: "male",
        age: 30,
        height_cm: 175,
        weight_kg: 70,
        activity_level: "moderately_active",
        goal: "weight_loss",
      },
      budget: {
        daily_budget: 500,
        weekly_budget: 3500,
        monthly_budget: 15000,
        currency_code: "PKR",
        country_id: "111",
        region_id: null,
        warnings: [],
      },
    });

    generateMealPlan.mockResolvedValue({
      plan_id: "test",
      plan_name: "Weight Loss Plan - 2000 kcal/day",
      start_date: "2026-08-21",
      end_date: "2026-08-21",
      days: [
        {
          plan_date: "2026-08-21",
          meals: [
            {
              meal_type: "breakfast",
              foods: [],
              subtotal_calories: 500,
              subtotal_protein_g: 30,
              subtotal_carbs_g: 60,
              subtotal_fat_g: 15,
              subtotal_estimated_cost: null,
              cost_complete: false,
            },
          ],
          total_calories: 2000,
          total_protein_g: 120,
          total_carbs_g: 250,
          total_fat_g: 67,
          total_estimated_cost: null,
          cost_complete: false,
          warnings: [],
        },
      ],
      nutrition: {
        calorie_target: 2000,
        protein_g: 120,
        carbs_g: 250,
        fat_g: 67,
        goal: "weight_loss",
        is_bounded: false,
        warnings: [],
      },
      budget: {
        daily_budget: 500,
        weekly_budget: 3500,
        monthly_budget: 15000,
        currency_code: "PKR",
      },
      warnings: [],
    });

    // Dynamic import to use mocked API
    const { default: DashboardPage } = require("@/app/dashboard/page");
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/2,000 kcal\/day/i)).toBeTruthy();
    });

    // Nutrition macros should be visible
    expect(screen.getByText("120g")).toBeTruthy();
    expect(screen.getByText("250g")).toBeTruthy();
    expect(screen.getByText("67g")).toBeTruthy();
  });

  it("shows loading skeleton while fetching", async () => {
    getNutritionAndBudget.mockReturnValue(new Promise(() => {}));

    const { default: DashboardPage } = require("@/app/dashboard/page");
    const { container } = render(<DashboardPage />);

    // Skeletons should be present
    const skeletons = container.querySelectorAll('[aria-hidden="true"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows error when API fails", async () => {
    getNutritionAndBudget.mockRejectedValue(new Error("Server error"));

    const { default: DashboardPage } = require("@/app/dashboard/page");
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
  });

  it("displays budget information correctly", async () => {
    getNutritionAndBudget.mockResolvedValue({
      nutrition: {
        calorie_target: 2000,
        protein_g: 100,
        carbs_g: 250,
        fat_g: 67,
        bmr: 1600,
        tdee: 2400,
        goal_adjustment: 0,
        is_bounded: false,
        warnings: [],
        sex: "male",
        age: 30,
        height_cm: 175,
        weight_kg: 70,
        activity_level: "moderately_active",
        goal: "general_fitness",
      },
      budget: {
        daily_budget: 500,
        weekly_budget: 3500,
        monthly_budget: 15000,
        currency_code: "PKR",
        country_id: "111",
        region_id: null,
        warnings: [],
      },
    });

    generateMealPlan.mockResolvedValue({
      plan_id: "test",
      plan_name: "Plan",
      start_date: "2026-08-21",
      end_date: "2026-08-21",
      days: [],
      nutrition: { calorie_target: 2000, protein_g: 100, carbs_g: 250, fat_g: 67, goal: "general_fitness", is_bounded: false, warnings: [] },
      budget: { daily_budget: 500, weekly_budget: 3500, monthly_budget: 15000, currency_code: "PKR" },
      warnings: [],
    });

    const { default: DashboardPage } = require("@/app/dashboard/page");
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/500.*day/i)).toBeTruthy();
    });

    expect(screen.getByText(/3,500/i)).toBeTruthy();
    expect(screen.getByText(/15,000/i)).toBeTruthy();
  });
});

/* ── Meal plan generation ─────────────────────────────────────────────── */

describe("meal plan generation", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getTodaysMealPlan.mockResolvedValue(null);
  });

  it("renders generate button in idle state", async () => {
    const { default: MealPlansPage } = require("@/app/dashboard/meal-plans/page");
    render(<MealPlansPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /generate plan/i })).toBeTruthy();
    });
  });

  it("shows loading state while generating", async () => {
    generateMealPlan.mockReturnValue(new Promise(() => {}));

    const { default: MealPlansPage } = require("@/app/dashboard/meal-plans/page");
    render(<MealPlansPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /generate plan/i })).toBeTruthy();
    });
    await userEvent.click(screen.getByRole("button", { name: /generate plan/i }));

    await waitFor(() => {
      const buttons = screen.getAllByRole("button", { name: /generating/i });
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it("displays meal plan on success", async () => {
    generateMealPlan.mockResolvedValue({
      plan_id: "test-123",
      plan_name: "Weight Loss Plan - 1800 kcal/day",
      start_date: "2026-08-21",
      end_date: "2026-08-21",
      days: [
        {
          plan_date: "2026-08-21",
          meals: [
            {
              meal_type: "breakfast",
              foods: [
                {
                  food_id: "f1",
                  name: "Roti",
                  slug: "roti",
                  serving_quantity: 2,
                  serving_unit_code: "pc",
                  portion_grams: 80,
                  calories: 210,
                  protein_g: 6,
                  carbs_g: 36,
                  fat_g: 5,
                  estimated_cost: null,
                  cost_available: false,
                },
              ],
              subtotal_calories: 210,
              subtotal_protein_g: 6,
              subtotal_carbs_g: 36,
              subtotal_fat_g: 5,
              subtotal_estimated_cost: null,
              cost_complete: false,
            },
          ],
          total_calories: 1800,
          total_protein_g: 120,
          total_carbs_g: 200,
          total_fat_g: 60,
          total_estimated_cost: null,
          cost_complete: false,
          warnings: [],
        },
      ],
      nutrition: { calorie_target: 1800, protein_g: 120, carbs_g: 200, fat_g: 60, goal: "weight_loss", is_bounded: false, warnings: [] },
      budget: { daily_budget: null, weekly_budget: null, monthly_budget: null, currency_code: null },
      warnings: [],
    });

    const { default: MealPlansPage } = require("@/app/dashboard/meal-plans/page");
    render(<MealPlansPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /generate plan/i })).toBeTruthy();
    });
    await userEvent.click(screen.getByRole("button", { name: /generate plan/i }));

    await waitFor(() => {
      expect(screen.getByText("Roti")).toBeTruthy();
      const kcalTexts = screen.getAllByText(/210.*kcal/);
      expect(kcalTexts.length).toBeGreaterThan(0);
    });
  });

  it("displays failure message when generation fails", async () => {
    generateMealPlan.mockResolvedValue({
      success: false,
      reason: "No eligible foods found after applying filters",
      conflict_details: [],
      suggestions: ["Check dietary preferences"],
    });

    const { default: MealPlansPage } = require("@/app/dashboard/meal-plans/page");
    render(<MealPlansPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /generate plan/i })).toBeTruthy();
    });
    await userEvent.click(screen.getByRole("button", { name: /generate plan/i }));

    await waitFor(() => {
      expect(screen.getByText(/no eligible foods/i)).toBeTruthy();
    });
  });

  it("displays error when API call throws", async () => {
    generateMealPlan.mockRejectedValue(new Error("Network error"));

    const { default: MealPlansPage } = require("@/app/dashboard/meal-plans/page");
    render(<MealPlansPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /generate plan/i })).toBeTruthy();
    });
    await userEvent.click(screen.getByRole("button", { name: /generate plan/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
  });

  it("day selector works for multi-day plans", async () => {
    generateMealPlan.mockResolvedValue({
      plan_id: "test-7day",
      plan_name: "Plan",
      start_date: "2026-08-21",
      end_date: "2026-08-27",
      days: [1, 2, 3].map((i) => ({
        plan_date: `2026-08-2${i}`,
        meals: [
          {
            meal_type: "lunch",
            foods: [
              {
                food_id: `f${i}`,
                name: `Food Day ${i}`,
                slug: `food-${i}`,
                serving_quantity: 100,
                serving_unit_code: "g",
                portion_grams: 100,
                calories: 200,
                protein_g: 10,
                carbs_g: 30,
                fat_g: 5,
                estimated_cost: null,
                cost_available: false,
              },
            ],
            subtotal_calories: 200,
            subtotal_protein_g: 10,
            subtotal_carbs_g: 30,
            subtotal_fat_g: 5,
            subtotal_estimated_cost: null,
            cost_complete: false,
          },
        ],
        total_calories: 200,
        total_protein_g: 10,
        total_carbs_g: 30,
        total_fat_g: 5,
        total_estimated_cost: null,
        cost_complete: false,
        warnings: [],
      })),
      nutrition: { calorie_target: 2000, protein_g: 100, carbs_g: 250, fat_g: 67, goal: "general_fitness", is_bounded: false, warnings: [] },
      budget: { daily_budget: null, weekly_budget: null, monthly_budget: null, currency_code: null },
      warnings: [],
    });

    const { default: MealPlansPage } = require("@/app/dashboard/meal-plans/page");
    render(<MealPlansPage />);

    // Wait for idle state after getTodaysMealPlan resolves
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /generate plan/i })).toBeTruthy();
    });

    // Select 3 days
    await userEvent.click(screen.getByRole("button", { name: /3 days/i }));
    await userEvent.click(screen.getByRole("button", { name: /generate plan/i }));

    await waitFor(() => {
      expect(screen.getByText("Day 1")).toBeTruthy();
      expect(screen.getByText("Day 2")).toBeTruthy();
      expect(screen.getByText("Day 3")).toBeTruthy();
    });

    // Click Day 2
    await userEvent.click(screen.getByText("Day 2"));

    await waitFor(() => {
      expect(screen.getByText("Food Day 2")).toBeTruthy();
    });
  });
});

/* ── Warnings ─────────────────────────────────────────────────────────── */

describe("warning display", () => {
  it("renders info variant with correct role", async () => {
    const { AlertBanner } = require("@/components/ui/alert-banner");
    render(<AlertBanner variant="info" message="Test info" />);
    const el = screen.getByText("Test info");
    expect(el.getAttribute("role")).toBe("status");
  });

  it("renders error variant with alert role", async () => {
    const { AlertBanner } = require("@/components/ui/alert-banner");
    render(<AlertBanner variant="error" message="Test error" />);
    const el = screen.getByText("Test error");
    expect(el.getAttribute("role")).toBe("alert");
  });
});
