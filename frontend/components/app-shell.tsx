"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getCurrentUser, logoutUser, type AuthUser } from "@/lib/api";
import { setUserState } from "@/lib/user-state";

const navItems = [
  {
    href: "/dashboard",
    label: "Home",
    icon: (
      <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    ),
  },
  {
    href: "/dashboard/meal-plans",
    label: "Meals",
    icon: (
      <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
  },
  {
    href: "/dashboard/saved-plans",
    label: "Saved",
    icon: (
      <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
      </svg>
    ),
  },
  {
    href: "/dashboard/food",
    label: "Food",
    icon: (
      <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
      </svg>
    ),
  },
  {
    href: "/dashboard/progress",
    label: "Progress",
    icon: (
      <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
      </svg>
    ),
  },
  {
    href: "/dashboard/settings",
    label: "Settings",
    icon: (
      <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
    <div className="dark flex min-h-screen flex-col bg-[#05050A] text-[#FFFFFF]">
      {/* ── Top Bar ─────────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between border-b border-white/8 bg-[#05050A]/80 px-5 py-3 backdrop-blur-xl md:px-8">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#DC143C] to-[#7B61FF] text-[10px] font-bold text-[#05050A]">
            <span className="relative z-10">SA</span>
          </div>
          <span className="hidden font-serif text-lg font-semibold tracking-tight text-[#FFFFFF] sm:inline">
            South Asian Fitness
          </span>
        </Link>

        <div className="flex items-center gap-4">
          {/* Tier badge */}
          {user && (
            <div
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-semibold tracking-wide uppercase ${
                isPro
                  ? "border border-[#DC143C]/30 bg-[#DC143C]/10 text-[#FF4060] animate-pulse-glow"
                  : "border border-white/10 bg-white/4 text-[#5A5A64]"
              }`}
            >
              <span className={`h-1 w-1 rounded-full ${isPro ? "bg-[#DC143C]" : "bg-[#64748B]"}`} />
              {isPro ? "Pro" : "Free"}
            </div>
          )}

          {/* User avatar */}
          <div className="hidden items-center gap-2 md:flex">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-[#DC143C]/20 to-[#7B61FF]/20 text-[10px] font-semibold text-[#FF4060]">
              {user?.display_name?.charAt(0)?.toUpperCase() || "?"}
            </div>
            <button
              onClick={handleLogout}
              className="rounded-full p-1 text-[#5A5A64] transition-colors hover:bg-white/5 hover:text-[#8A8A94]"
              title="Log out"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ────────────────────────────────────────────── */}
      <main className="flex-1 pt-16 pb-24 md:pb-8">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 md:px-8 lg:px-12">{children}</div>
      </main>

      {/* ── Floating Bottom Dock ─────────────────────────────────────── */}
      <nav className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 md:bottom-6">
        <div className="flex items-center gap-1 rounded-2xl border border-white/10 bg-[#05050A]/90 px-2 py-2 shadow-[0_8px_32px_rgba(0,0,0,0.5)] backdrop-blur-xl">
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
                className={`group relative flex flex-col items-center gap-1 rounded-xl px-3 py-2 transition-all duration-300 md:px-4 ${
                  isActive
                    ? "text-[#DC143C]"
                    : "text-[#5A5A64] hover:text-[#8A8A94]"
                }`}
              >
                {isActive && (
                  <span className="absolute inset-0 rounded-xl bg-[#DC143C]/10" />
                )}
                <span className="relative z-10">{item.icon}</span>
                <span className="relative z-10 text-[9px] font-medium tracking-wide md:text-[10px]">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
