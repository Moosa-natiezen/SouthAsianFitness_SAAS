import { Skeleton } from "@/components/ui/skeleton";

/**
 * Sleek skeleton loader that imitates the meal plan card shape
 * while the AI generates content.
 */
export function MealPlanSkeleton() {
  return (
    <div className="space-y-4">
      {/* Header skeleton */}
      <div className="flex items-center gap-3">
        <Skeleton className="h-3 w-24 rounded-full bg-stone-200 dark:bg-zinc-800" />
        <Skeleton className="h-5 w-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30" />
      </div>

      {/* Day heading skeleton */}
      <Skeleton className="h-5 w-20 rounded-md bg-stone-200 dark:bg-zinc-800" />

      {/* Meal card skeletons — 3 meals per day */}
      {[1, 2, 3].map((meal) => (
        <div
          key={meal}
          className="rounded-2xl border border-stone-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 space-y-3"
        >
          {/* Meal label */}
          <Skeleton className="h-3 w-16 rounded-full bg-stone-200 dark:bg-zinc-800" />

          {/* Dish name */}
          <Skeleton className="h-4 w-40 rounded-md bg-stone-200 dark:bg-zinc-800" />

          {/* Macro pills */}
          <div className="flex gap-2">
            <Skeleton className="h-6 w-16 rounded-lg bg-emerald-50 dark:bg-emerald-900/20" />
            <Skeleton className="h-6 w-16 rounded-lg bg-stone-100 dark:bg-zinc-800" />
            <Skeleton className="h-6 w-16 rounded-lg bg-stone-100 dark:bg-zinc-800" />
          </div>

          {/* Description lines */}
          <div className="space-y-2 pt-1">
            <Skeleton className="h-3 w-full rounded bg-stone-100 dark:bg-zinc-800" />
            <Skeleton className="h-3 w-3/4 rounded bg-stone-100 dark:bg-zinc-800" />
          </div>
        </div>
      ))}

      {/* Total macros bar skeleton */}
      <div className="rounded-xl bg-stone-50 dark:bg-zinc-800 p-4">
        <Skeleton className="h-3 w-28 rounded-full bg-stone-200 dark:bg-zinc-700" />
        <div className="mt-3 flex gap-4">
          <Skeleton className="h-8 w-16 rounded-lg bg-emerald-50 dark:bg-emerald-900/20" />
          <Skeleton className="h-8 w-16 rounded-lg bg-stone-100 dark:bg-zinc-700" />
          <Skeleton className="h-8 w-16 rounded-lg bg-stone-100 dark:bg-zinc-700" />
          <Skeleton className="h-8 w-16 rounded-lg bg-stone-100 dark:bg-zinc-700" />
        </div>
      </div>

      {/* Pulsing loading indicator */}
      <div className="flex items-center justify-center gap-2 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-500 [animation-delay:0ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-500 [animation-delay:150ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-500 [animation-delay:300ms]" />
        <span className="ml-2 text-xs font-medium text-stone-400 dark:text-zinc-500">
          Generating your plan...
        </span>
      </div>
    </div>
  );
}
