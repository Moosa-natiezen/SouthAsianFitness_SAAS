import { cn } from "@/lib/utils";

type AlertBannerProps = {
  variant: "info" | "warning" | "error";
  message: string;
  className?: string;
};

const styles = {
  info: "border-blue-200 bg-blue-50 text-blue-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
  error: "border-red-200 bg-red-50 text-red-700",
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
