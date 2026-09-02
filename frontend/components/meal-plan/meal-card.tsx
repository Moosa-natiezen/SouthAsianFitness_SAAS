import type { GeneratedMeal } from "@/lib/api";

const mealEmoji: Record<string, string> = {
  breakfast: "🍳",
  lunch: "🍛",
  snack: "🥗",
  dinner: "🍲",
};

type MealCardProps = {
  meal: GeneratedMeal;
  currency: string | null;
};

export function MealCard({ meal, currency }: MealCardProps) {
  return (
    <article className="rounded-2xl glass p-5">
      {/* Meal header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white">
          {mealEmoji[meal.meal_type] ?? "🍽️"}{" "}
          {meal.meal_type.charAt(0).toUpperCase() + meal.meal_type.slice(1)}
        </h3>
        <span className="text-sm font-medium text-zinc-400">
          {Math.round(meal.subtotal_calories)} kcal
        </span>
      </div>

      {/* Foods */}
      <ul className="mt-3 divide-y divide-white/8">
        {meal.foods.map((food) => (
          <li key={food.food_id} className="flex items-center justify-between py-2 text-sm">
            <div>
              <span className="font-medium text-zinc-100">{food.name}</span>
              <span className="ml-2 text-zinc-400">
                {food.serving_quantity > 0
                  ? `${food.serving_quantity} ${food.serving_unit_code}`
                  : `${food.portion_grams}g`}
              </span>
            </div>
            <div className="flex items-center gap-3 text-zinc-400">
              <span>{Math.round(food.calories)} kcal</span>
              {food.cost_available && food.estimated_cost !== null && currency && (
                <span className="text-zinc-400">
                  {currency} {Number(food.estimated_cost).toFixed(0)}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>

      {/* Subtotals */}
      <div className="mt-3 flex items-center justify-between border-t border-white/10 pt-3">
        <div className="flex gap-3 text-xs text-zinc-400">
          <span>P {Math.round(meal.subtotal_protein_g)}g</span>
          <span>C {Math.round(meal.subtotal_carbs_g)}g</span>
          <span>F {Math.round(meal.subtotal_fat_g)}g</span>
        </div>
        {meal.subtotal_estimated_cost !== null && currency && (
          <span className="text-sm text-zinc-400">
            {currency} {Number(meal.subtotal_estimated_cost).toLocaleString()}
          </span>
        )}
      </div>
    </article>
  );
}
