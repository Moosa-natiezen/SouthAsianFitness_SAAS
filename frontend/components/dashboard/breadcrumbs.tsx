"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

/** Friendly labels for known segments; unknown segments fall back to
 *  a title-cased version of the raw path segment. */
const segmentLabels: Record<string, string> = {
  dashboard: "Dashboard",
  "meal-plans": "Meal Plan",
  "saved-plans": "Saved Plans",
  workouts: "Workouts",
  food: "Food Library",
  progress: "Progress",
  settings: "Settings",
};

function labelForSegment(segment: string): string {
  const known = segmentLabels[segment];
  if (known) return known;
  return segment
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Minimal breadcrumb navigation for dashboard views, e.g.
 *   Dashboard / Meal Plan / Generate
 * Built from usePathname(); the current page renders as plain text
 * (aria-current="page"), every ancestor as a clickable link.
 */
export function Breadcrumbs({ className }: { className?: string }) {
  const pathname = usePathname() ?? "/";

  // "/dashboard/meal-plans/day-3" → ["dashboard", "meal-plans", "day-3"]
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return null;

  const crumbs = segments.map((segment, index) => ({
    segment,
    href: `/${segments.slice(0, index + 1).join("/")}`,
    label: labelForSegment(segment),
    isLast: index === segments.length - 1,
  }));

  return (
    <nav aria-label="Breadcrumb" className={cn("print:hidden", className)}>
      <ol className="flex flex-wrap items-center gap-1.5 text-xs text-stone-400 dark:text-zinc-500">
        {crumbs.map(({ href, label, isLast }) => (
          <li key={href} className="flex items-center gap-1.5">
            {isLast ? (
              <span aria-current="page" className="font-medium text-stone-600 dark:text-zinc-300">
                {label}
              </span>
            ) : (
              <Link
                href={href}
                className="transition-colors duration-200 hover:text-emerald-600 dark:hover:text-emerald-400"
              >
                {label}
              </Link>
            )}
            {!isLast && (
              <span aria-hidden="true" className="select-none text-stone-300 dark:text-zinc-600">
                /
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
