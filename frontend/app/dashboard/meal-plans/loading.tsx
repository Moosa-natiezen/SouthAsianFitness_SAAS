import { Skeleton } from "@/components/ui/skeleton";

/** Instant shell while /dashboard/meal-plans's data fetches on navigation. */
export default function MealPlansLoading() {
  return (
    <div className="space-y-4">
      {/* Page heading */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-48 rounded-md" />
        <Skeleton className="h-4 w-64 rounded-md" />
      </div>

      {/* Plan card */}
      <div className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <Skeleton className="h-3 w-24 rounded-full" />
        <Skeleton className="mt-3 h-5 w-56 rounded-md" />
        <Skeleton className="mt-2 h-3 w-40 rounded-md" />
      </div>

      {/* Day selector strip */}
      <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4 dark:border-zinc-800 dark:bg-zinc-900/50">
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-14 w-20 rounded-lg" />
          ))}
        </div>
      </div>

      {/* Meal cards */}
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-stone-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-24 rounded-md" />
              <Skeleton className="h-3 w-16 rounded-full" />
            </div>
            <div className="mt-4 space-y-2.5">
              {[1, 2].map((j) => (
                <div key={j} className="flex items-center justify-between">
                  <Skeleton className="h-4 w-44 rounded-md" />
                  <Skeleton className="h-3 w-20 rounded-full" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
