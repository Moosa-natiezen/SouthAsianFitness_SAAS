import { Skeleton } from "@/components/ui/skeleton";

/** Instant shell while /dashboard/saved-plans's data fetches on navigation. */
export default function SavedPlansLoading() {
  return (
    <div className="space-y-4">
      {/* Page heading */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-48 rounded-md" />
        <Skeleton className="h-4 w-64 rounded-md" />
      </div>

      {/* Saved plan cards */}
      <div className="space-y-2.5">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-stone-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="flex items-center justify-between">
              <Skeleton className={`h-4 ${i % 2 === 0 ? "w-44" : "w-60"} rounded-md`} />
              <Skeleton className="h-3 w-16 rounded-full" />
            </div>
            <div className="mt-3 flex gap-2">
              <Skeleton className="h-3 w-20 rounded-full" />
              <Skeleton className="h-3 w-20 rounded-full" />
              <Skeleton className="h-3 w-20 rounded-full" />
</div>
            <Skeleton className="mt-3 h-9 w-28 rounded-xl" />
          </div>
        ))}
      </div>
    </div>
  );
}
