import { Skeleton } from "@/components/ui/skeleton";

/** Instant shell while /dashboard/progress's data fetches on navigation. */
export default function ProgressLoading() {
  return (
    <div className="space-y-4">
      {/* Page heading */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-44 rounded-md" />
        <Skeleton className="h-4 w-64 rounded-md" />
      </div>

      {/* Summary stat cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-stone-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <Skeleton className="h-3 w-16 rounded-full" />
            <Skeleton className="mt-3 h-6 w-16 rounded-md" />
          </div>
        ))}
      </div>

      {/* Chart card */}
      <div className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <Skeleton className="h-4 w-36 rounded-md" />
        <Skeleton className="mt-4 h-64 w-full rounded-xl" />
      </div>

      {/* Log entry rows */}
      <div className="space-y-2.5">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="flex items-center justify-between rounded-2xl border border-stone-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <Skeleton className="h-4 w-40 rounded-md" />
            <Skeleton className="h-4 w-14 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
