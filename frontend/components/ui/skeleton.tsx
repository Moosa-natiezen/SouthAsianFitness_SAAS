import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "animate-pulse rounded-lg bg-stone-100 dark:bg-zinc-800",
        className,
      )}
      {...props}
    />
  );
}

export { Skeleton };
