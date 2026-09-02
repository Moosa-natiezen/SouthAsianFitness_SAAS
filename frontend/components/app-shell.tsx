"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getCurrentUser, logoutUser, type AuthUser } from "@/lib/api";
import { setUserState } from "@/lib/user-state";

const navItems = [
  { href: "/dashboard", label: "Home", icon: "ホーム" },
  { href: "/dashboard/meal-plans", label: "Meals", icon: "食事" },
  { href: "/dashboard/saved-plans", label: "Saved", icon: "保存" },
  { href: "/dashboard/workouts", label: "Workouts", icon: "運動" },
  { href: "/dashboard/food", label: "Food", icon: "食料" },
  { href: "/dashboard/progress", label: "Progress", icon: "記録" },
  { href: "/dashboard/settings", label: "Settings", icon: "設定" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then((u) => {
        setUser(u);
        setUserState(u);
      })
      .catch(() => {});
  }, []);

  const handleLogout = async () => {
    try {
      await logoutUser();
      router.push("/auth/login");
      router.refresh();
    } catch {
      router.push("/auth/login");
    }
  };

  const isPro = user?.subscription_tier === "pro";

  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa]">
      {/* ── Top Bar ─────────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between border-b border-white/8 bg-[#09090b]/80 backdrop-blur-md">
        <div className="flex items-center gap-3 px-5 py-3 md:px-8">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-white text-[10px] font-bold text-[#09090b]">
              SA
            </div>
            <span className="hidden text-sm font-semibold sm:inline">South Asian Fitness</span>
          </Link>
        </div>

        <div className="flex items-center gap-4 px-5 py-3 md:px-8">
          {user && (
            <span className="text-xs text-zinc-500">
              {isPro ? "Pro" : "Free"}
            </span>
          )}
          <div className="hidden items-center gap-3 md:flex">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/[0.06] text-[10px] font-medium text-zinc-400">
              {user?.display_name?.charAt(0)?.toUpperCase() || "?"}
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ────────────────────────────────────────────── */}
      <main className="pt-14 pb-24 md:pb-8">
        <div className="mx-auto max-w-5xl px-5 py-6 md:px-8">{children}</div>
      </main>

      {/* ── Bottom Nav ──────────────────────────────────────────────── */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-white/8 bg-[#09090b]/90 backdrop-blur-md md:bottom-auto md:top-14 md:left-0 md:right-auto md:h-[calc(100vh-3.5rem)] md:w-16 md:border-t-0 md:border-r md:flex md:flex-col md:items-center md:pt-4">
        <div className="flex items-center gap-1 px-2 py-2 md:flex-col md:gap-1 md:px-0">
          {navItems.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`flex flex-col items-center gap-0.5 rounded-lg px-3 py-2 text-[10px] transition-colors md:px-0 md:py-2.5 ${
                  isActive
                    ? "text-white"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <span className="text-base leading-none">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
