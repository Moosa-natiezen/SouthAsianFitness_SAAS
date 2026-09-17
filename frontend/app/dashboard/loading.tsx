import { Skeleton } from "@/components/ui/skeleton";

/** Instant shell while /dashboard's data fetches on navigation. */
export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      {/* Greeting block */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-56 rounded-md" />
        <Skeleton className="h-4 w-72 rounded-md" />
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-stone-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <Skeleton className="h-3 w-16 rounded-full" />
            <Skeleton className="mt-3 h-7 w-20 rounded-md" />
          </div>
        ))}
      </div>

      {/* Today's plan preview */}
      <div className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <Skeleton className="h-4 w-32 rounded-md" />
        <div className="mt-4 space-y-3">
          <Skeleton className="h-4 w-3/4 rounded-md" />
          <Skeleton className="h-4 w-1/2 rounded-md" />
        </div>
        <div className="mt-5 flex gap-3">
          <Skeleton className="h-9 w-32 rounded-xl" />
          <Skeleton className="h-9 w-32 rounded-xl" />
        </div>
      </div>
    </div>
  );
}
