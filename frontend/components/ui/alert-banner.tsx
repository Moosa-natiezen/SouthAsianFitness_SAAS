import { cn } from "@/lib/utils";

type AlertBannerProps = {
  variant: "info" | "warning" | "error";
  message: string;
  className?: string;
};

const styles = {
  info: "border-orange-600/15 bg-orange-600/5 text-orange-600",
  warning: "border-amber-500/15 bg-amber-500/5 text-amber-300",
  error: "border-red-500/15 bg-red-500/5 text-red-300",
} as const;

export function AlertBanner({ variant, message, className }: AlertBannerProps) {
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      aria-live="polite"
      className={cn(
        "rounded-xl border px-4 py-3 text-sm",
        styles[variant],
        className,
      )}
    >
      {message}
    </div>
  );
}
