"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { logoutUser } from "@/lib/api";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/meal-plans", label: "Meal Plans" },
  { href: "/dashboard/food", label: "Food" },
  { href: "/dashboard/progress", label: "Progress" },
  { href: "/dashboard/settings", label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await logoutUser();
      router.push("/auth/login");
      router.refresh();
    } catch {
      router.push("/auth/login");
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-200 bg-white lg:w-72 lg:border-b-0 lg:border-r">
          <div className="flex items-center justify-between px-6 py-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-sm font-bold text-white">
                SA
              </div>
              <div>
                <p className="font-semibold">South Asian Fitness</p>
              </div>
            </div>
          </div>

          <nav className="flex flex-wrap gap-2 px-4 pb-4 lg:flex-col lg:px-4 lg:pb-8">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-xl px-3 py-2 text-sm font-medium transition ${
                    isActive
                      ? "bg-emerald-50 text-emerald-700"
                      : "text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="flex-1">
          <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-4 sm:px-6">
            <div>
              <p className="text-sm uppercase tracking-[0.12em] text-slate-500">Workspace</p>
              <h1 className="text-xl font-semibold">Your app</h1>
            </div>
            <Button variant="outline" onClick={handleLogout}>
              Log out
            </Button>
          </header>
          <div className="p-4 sm:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
