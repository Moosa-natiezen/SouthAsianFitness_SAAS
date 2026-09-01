"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getCurrentUser, logoutUser, type AuthUser } from "@/lib/api";
import { setUserState } from "@/lib/user-state";

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
      </svg>
    ),
  },
  {
    href: "/dashboard/meal-plans",
    label: "Meal Plans",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
  },
  {
    href: "/dashboard/food",
    label: "Food Library",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
      </svg>
    ),
  },
  {
    href: "/dashboard/progress",
    label: "Progress",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
      </svg>
    ),
  },
  {
    href: "/dashboard/settings",
    label: "Settings",
    icon: (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
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
    <div className="dark flex min-h-screen bg-[#09090b] text-zinc-100">
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="hidden lg:flex lg:w-72 lg:flex-col lg:border-r lg:border-white/[0.06] lg:bg-[#09090b]/80 lg:backdrop-blur-xl">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-6">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-400 text-sm font-bold text-white shadow-lg shadow-emerald-500/20">
            <span className="relative z-10">SA</span>
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-400 opacity-50 blur-md" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">South Asian Fitness</p>
            <p className="text-[11px] text-zinc-500">Powered by AI</p>
          </div>
        </div>

        {/* Tier badge */}
        {user && (
          <div className="mx-4 mb-4">
            <div
              className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition-all ${
                isPro
                  ? "border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 animate-pulse-glow"
                  : "border border-white/[0.06] bg-white/[0.03] text-zinc-400"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${isPro ? "bg-emerald-400" : "bg-zinc-500"}`}
              />
              {isPro ? "Pro Plan" : "Free Plan"}
              {isPro && (
                <span className="ml-auto rounded-md bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-300">
                  UNLIMITED
                </span>
              )}
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav aria-label="Main navigation" className="flex-1 space-y-1 px-3">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-emerald-500/10 text-emerald-400 shadow-[inset_0_0_20px_rgba(16,185,129,0.05)]"
                    : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-200"
                }`}
              >
                <span
                  className={`transition-colors ${
                    isActive ? "text-emerald-400" : "text-zinc-500 group-hover:text-zinc-300"
                  }`}
                >
                  {item.icon}
                </span>
                {item.label}
                {isActive && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-white/[0.06] p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 text-xs font-semibold text-emerald-300">
              {user?.display_name?.charAt(0)?.toUpperCase() || "?"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-zinc-200">
                {user?.display_name || "Loading..."}
              </p>
              <p className="truncate text-[11px] text-zinc-500">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-1.5 text-zinc-500 transition-colors hover:bg-white/[0.06] hover:text-zinc-300"
              title="Log out"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* ── Mobile header ──────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-white/[0.06] bg-[#09090b]/80 px-4 py-3 backdrop-blur-xl lg:hidden">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-400 text-[10px] font-bold text-white">
              SA
            </div>
            <span className="text-sm font-semibold text-white">SA Fitness</span>
          </Link>
          <Button variant="ghost" size="sm" onClick={handleLogout} className="text-zinc-400 hover:text-white">
            Log out
          </Button>
        </header>

        {/* ── Main content ─────────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
