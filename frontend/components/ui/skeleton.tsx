import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "animate-pulse rounded-lg bg-white/6",
        className,
      )}
      {...props}
    />
  );
}

export { Skeleton };
