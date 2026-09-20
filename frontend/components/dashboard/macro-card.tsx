import { cn } from "@/lib/utils";

type MacroCardProps = {
  label: string;
  value: string | number;
  unit?: string;
  sublabel?: string;
  /** Highlight the metric value with the amber-gradient text clip. */
  accent?: boolean;
  className?: string;
};

/**
 * Reusable glassmorphism metric card for the dashboard.
 *
 * Surface: `bg-dark-surface` (theme-aware card token) with backdrop blur;
 * hover: sub-200ms elevation/scale for a native-app feel.
 */
export function MacroCard({
  label,
  value,
  unit,
  sublabel,
  accent = false,
  className,
}: MacroCardProps) {
  return (
    <div
      className={cn(
        "group rounded-2xl border border-dark-border bg-dark-surface/80 p-5 backdrop-blur-md",
        "transition-all duration-150 ease-out",
        "hover:-translate-y-0.5 hover:scale-[1.02] hover:shadow-lg hover:shadow-amber-500/10",
        accent && "border-amber-500/30",
        className,
      )}
    >
      <p className="text-xs font-medium uppercase tracking-[0.15em] text-stone-500 dark:text-zinc-400">
        {label}
      </p>
      <div className="mt-3 flex items-baseline gap-1.5">
        <span
          className={cn(
            "text-3xl font-bold tabular-nums",
            accent ? "amber-gradient" : "text-stone-900 dark:text-zinc-100",
          )}
        >
          {value}
        </span>
        {unit && (
          <span className="text-sm text-stone-400 dark:text-zinc-500">{unit}</span>
        )}
      </div>
      {sublabel && (
        <p className="mt-2 text-xs text-stone-500 dark:text-zinc-500">{sublabel}</p>
      )}
    </div>
  );
}
