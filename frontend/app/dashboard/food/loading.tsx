import { Skeleton } from "@/components/ui/skeleton";

/** Instant shell while /dashboard/food's data fetches on navigation. */
export default function FoodLoading() {
  return (
    <div className="space-y-4">
      {/* Page heading */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-40 rounded-md" />
        <Skeleton className="h-4 w-60 rounded-md" />
      </div>

      {/* Search bar + category chips */}
      <div className="space-y-3">
        <Skeleton className="h-11 w-full rounded-xl" />
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-8 w-20 rounded-full" />
          ))}
        </div>
      </div>

      {/* Food result rows with thumbnails */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-2xl border border-stone-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <Skeleton className="h-14 w-14 rounded-xl" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-32 rounded-md" />
              <Skeleton className="h-3 w-24 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
