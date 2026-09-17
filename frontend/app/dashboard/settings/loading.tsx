import { Skeleton } from "@/components/ui/skeleton";

/** Instant shell while /dashboard/settings's data fetches on navigation. */
export default function SettingsLoading() {
  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-40 rounded-md" />
        <Skeleton className="h-4 w-64 rounded-md" />
      </div>

      {/* Settings section cards */}
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <Skeleton className="h-4 w-36 rounded-md" />
            <div className="mt-4 space-y-3">
              <Skeleton className="h-11 w-full rounded-xl" />
              <Skeleton className="h-11 w-full rounded-xl" />
              <Skeleton className="h-9 w-32 rounded-xl" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
