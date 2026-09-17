import { Skeleton } from "@/components/ui/skeleton";

/** Instant shell while /dashboard/workouts's data fetches on navigation. */
export default function WorkoutsLoading() {
  return (
    <div className="space-y-4">
      {/* Page heading */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-52 rounded-md" />
        <Skeleton className="h-4 w-60 rounded-md" />
      </div>

      {/* Saved workout rows with staggered widths */}
      <div className="space-y-2.5">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-stone-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="flex items-center justify-between">
              <Skeleton className={`h-4 ${i % 2 === 0 ? "w-40" : "w-56"} rounded-md`} />
              <Skeleton className="h-3 w-16 rounded-full" />
            </div>
            <div className="mt-3 flex gap-2">
              <Skeleton className="h-3 w-24 rounded-full" />
              <Skeleton className="h-3 w-24 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
