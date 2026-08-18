import Link from "next/link";

import { Button } from "@/components/ui/button";

const goals = [
  "Weight loss",
  "Weight gain",
  "Muscle building",
  "General fitness",
];

const principles = [
  "Traditional South Asian meals remain realistic and enjoyable.",
  "Budget-conscious plans designed for everyday life.",
  "Flexible guidance across multiple countries and regions.",
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.12),_transparent_40%),linear-gradient(to_bottom,_#f8fafc,_#eef2ff)] text-slate-900">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 font-bold text-white shadow-sm">
            SA
          </div>
          <div>
            <p className="text-lg font-semibold">South Asian Fitness</p>
          </div>
        </div>
        <nav className="hidden items-center gap-6 text-sm font-medium text-slate-700 md:flex">
          <Link href="#benefits">Benefits</Link>
          <Link href="#goals">Goals</Link>
          <Link href="#about">About</Link>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/auth/login">
            <Button variant="ghost" size="sm">Log in</Button>
          </Link>
          <Link href="/auth/signup">
            <Button size="sm">Get started</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-16 px-6 pb-16 pt-8 md:pt-14">
        <section className="grid items-center gap-10 md:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-8">
            <div className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">
              Personalized for real life, not restrictive diets
            </div>

            <div className="space-y-5">
              <h1 className="max-w-xl text-4xl font-bold tracking-tight text-slate-900 md:text-6xl">
                Get fit without giving up your South Asian food.
              </h1>
              <p className="max-w-xl text-lg text-slate-700">
                Learn how to build a realistic fitness plan around the foods, meals,
                routines, and budgets that fit your life and your region.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <Link href="/auth/signup">
                <Button size="lg">Create account</Button>
              </Link>
              <Link href="/auth/login">
                <Button variant="outline" size="lg">
                  I already have an account
                </Button>
              </Link>
            </div>

            <div className="flex flex-wrap gap-4 text-sm text-slate-600">
              <span>Budget-conscious</span>
              <span>Multi-country support</span>
              <span>Flexible lifestyle goals</span>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
            <div className="space-y-5">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-500">Popular focus</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">Balanced nutrition, not elimination.</p>
              </div>
              <div className="space-y-3">
                {principles.map((item) => (
                  <div key={item} className="flex gap-3 rounded-xl border border-slate-200 p-3">
                    <div className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700">
                      ✓
                    </div>
                    <p className="text-sm text-slate-700">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="benefits" className="grid gap-6 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.08em] text-emerald-700">Smart personalization</p>
            <h2 className="mt-4 text-xl font-semibold">Built around your goals</h2>
            <p className="mt-2 text-slate-600">
              Choose a plan that matches your stage—fat loss, strength, weight gain, or sustainable everyday fitness.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.08em] text-emerald-700">Practical budgets</p>
            <h2 className="mt-4 text-xl font-semibold">Works with real spending</h2>
            <p className="mt-2 text-slate-600">
              Account for the foods and grocery budgets that fit your home, city, and local market realities.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.08em] text-emerald-700">Regional flexibility</p>
            <h2 className="mt-4 text-xl font-semibold">Multi-country ready</h2>
            <p className="mt-2 text-slate-600">
              Support for different regions, currencies, languages, and food traditions without forcing a one-size-fits-all model.
            </p>
          </div>
        </section>

        <section id="goals" className="rounded-3xl border border-slate-200 bg-slate-900 p-8 text-white shadow-xl">
          <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-300">Popular paths</p>
              <h2 className="mt-3 text-3xl font-semibold">Choose the goal that fits your life.</h2>
            </div>
            <Link href="/auth/signup">
              <Button variant="secondary" className="bg-white text-slate-900 hover:bg-slate-100">
                Start your profile
              </Button>
            </Link>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {goals.map((goal) => (
              <div key={goal} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-lg font-medium text-white">{goal}</p>
              </div>
            ))}
          </div>
        </section>

        <footer id="about" className="flex flex-col gap-4 border-t border-slate-200 py-6 text-sm text-slate-600 md:flex-row md:items-center md:justify-between">
          <p>© 2026 South Asian Fitness</p>
          <div className="flex gap-4">
            <Link href="/auth/login">Login</Link>
            <Link href="/auth/signup">Sign up</Link>
          </div>
        </footer>
      </main>
    </div>
  );
}
