import { Skeleton } from "@/components/ui/skeleton";

/**
 * Sleek skeleton loader that imitates the workout plan card shape.
 */
export function WorkoutPlanSkeleton() {
  return (
    <div className="space-y-4">
      {/* Terminal header skeleton */}
      <div className="flex items-center gap-2 border-b border-stone-200 dark:border-zinc-700 px-5 py-3">
        <Skeleton className="h-2.5 w-2.5 rounded-full bg-stone-200 dark:bg-zinc-700" />
        <Skeleton className="h-2.5 w-2.5 rounded-full bg-stone-200 dark:bg-zinc-700" />
        <Skeleton className="h-2.5 w-2.5 rounded-full bg-stone-200 dark:bg-zinc-700" />
        <Skeleton className="ml-2 h-3 w-32 rounded-full bg-stone-200 dark:bg-zinc-700" />
      </div>

      {/* Workout header */}
      <div className="px-6 pt-4 space-y-2">
        <Skeleton className="h-5 w-48 rounded-md bg-stone-200 dark:bg-zinc-800" />
        <Skeleton className="h-3 w-64 rounded bg-stone-100 dark:bg-zinc-800" />
      </div>

      {/* Day headings + exercise rows */}
      {[1, 2, 3].map((day) => (
        <div key={day} className="px-6 space-y-2">
          <Skeleton className="h-4 w-28 rounded-md bg-emerald-50 dark:bg-emerald-900/20" />
          <div className="space-y-1.5 pl-2">
            {[1, 2, 3, 4].map((ex) => (
              <div key={ex} className="flex items-center gap-3">
                <Skeleton className="h-3 w-3 rounded-full bg-stone-200 dark:bg-zinc-800" />
                <Skeleton className="h-3 w-32 rounded bg-stone-100 dark:bg-zinc-800" />
                <Skeleton className="h-3 w-12 rounded bg-stone-100 dark:bg-zinc-800 ml-auto" />
                <Skeleton className="h-3 w-10 rounded bg-stone-100 dark:bg-zinc-800" />
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Pulsing loading indicator */}
      <div className="flex items-center justify-center gap-2 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-500 [animation-delay:0ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-500 [animation-delay:150ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-emerald-500 [animation-delay:300ms]" />
        <span className="ml-2 text-xs font-medium text-stone-400 dark:text-zinc-500">
          Building your workout...
        </span>
      </div>
    </div>
  );
}
