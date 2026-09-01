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
    <div className="dark min-h-screen bg-[#09090b] text-zinc-100">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#c4854c] to-[#e8a838] text-sm font-bold text-[#f5f0e8] shadow-lg shadow-[#c4854c]/20">
            <span className="relative z-10">SA</span>
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-[#c4854c] to-[#e8a838] opacity-50 blur-md" />
          </div>
          <p className="text-lg font-semibold text-[#f5f0e8]">South Asian Fitness</p>
        </div>
        <nav className="hidden items-center gap-6 text-sm font-medium text-zinc-400 md:flex">
          <a href="#benefits" className="transition hover:text-[#f5f0e8]">Benefits</a>
          <a href="#goals" className="transition hover:text-[#f5f0e8]">Goals</a>
          <a href="#about" className="transition hover:text-[#f5f0e8]">About</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/auth/login">
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-[#f5f0e8]">Log in</Button>
          </Link>
          <Link href="/auth/signup">
            <Button size="sm" className="bg-gradient-to-r from-[#c4854c] to-[#e8a838] text-[#f5f0e8] shadow-lg shadow-[#c4854c]/20 hover:shadow-[#c4854c]/30">Get started</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-16 px-6 pb-16 pt-8 md:pt-14">
        {/* ── Hero Section ───────────────────────────────────────────── */}
        <section className="grid items-center gap-10 md:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-8">
            <div className="inline-flex items-center rounded-full border border-[#c4854c]/20 bg-[#c4854c]/10 px-3 py-1 text-sm font-medium text-[#d4a574]">
              ✨ Personalized for real life, not restrictive diets
            </div>

            <div className="space-y-5">
              <h1 className="max-w-xl text-4xl font-bold tracking-tight text-[#f5f0e8] md:text-6xl">
                Get fit without giving up your{" "}
                <span className="text-gradient-cardamom">South Asian food.</span>
              </h1>
              <p className="max-w-xl text-lg text-zinc-400">
                Learn how to build a realistic fitness plan around the foods, meals,
                routines, and budgets that fit your life and your region.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <Link href="/auth/signup">
                <Button size="lg" className="bg-gradient-to-r from-[#c4854c] to-[#e8a838] text-[#f5f0e8] shadow-lg shadow-[#c4854c]/20 hover:shadow-[#c4854c]/30">
                  Create account
                </Button>
              </Link>
              <Link href="/auth/login">
                <Button variant="outline" size="lg" className="border-white/[0.08] bg-white/[0.03] text-zinc-300 hover:bg-white/[0.06]">
                  I already have an account
                </Button>
              </Link>
            </div>

            <div className="flex flex-wrap gap-4 text-sm text-zinc-500">
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-[#c4854c]" />
                Budget-conscious
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-[#e8a838]" />
                Multi-country support
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-amber-400" />
                Flexible lifestyle goals
              </span>
            </div>
          </div>

          {/* Hero card */}
          <div className="relative overflow-hidden rounded-3xl glass-strong p-6">
            <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-[#c4854c]/10 blur-[60px]" />
            <div className="absolute -left-10 -bottom-10 h-40 w-40 rounded-full bg-[#e8a838]/5 blur-[60px]" />

            <div className="relative space-y-5">
              <div className="rounded-2xl bg-white/[0.04] p-4">
                <p className="text-sm font-medium text-zinc-500">Popular focus</p>
                <p className="mt-2 text-2xl font-semibold text-[#f5f0e8]">Balanced nutrition, not elimination.</p>
              </div>
              <div className="space-y-3">
                {principles.map((item) => (
                  <div key={item} className="flex gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                    <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#c4854c]/10 text-xs font-semibold text-[#d4a574]">
                      ✓
                    </div>
                    <p className="text-sm text-zinc-300">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── Benefits Section ────────────────────────────────────────── */}
        <section id="benefits" className="grid gap-6 md:grid-cols-3">
          <BenefitCard
            badge="Smart personalization"
            title="Built around your goals"
            description="Choose a plan that matches your stage—fat loss, strength, weight gain, or sustainable everyday fitness."
          />
          <BenefitCard
            badge="Practical budgets"
            title="Works with real spending"
            description="Account for the foods and grocery budgets that fit your home, city, and local market realities."
          />
          <BenefitCard
            badge="Regional flexibility"
            title="Multi-country ready"
            description="Support for different regions, currencies, languages, and food traditions without forcing a one-size-fits-all model."
          />
        </section>

        {/* ── Goals Section ───────────────────────────────────────────── */}
        <section id="goals" className="relative overflow-hidden rounded-3xl glass-strong p-8">
          <div className="absolute -right-20 -top-20 h-60 w-60 rounded-full bg-[#c4854c]/10 blur-[80px]" />
          <div className="absolute -left-20 -bottom-20 h-60 w-60 rounded-full bg-[#e8a838]/5 blur-[80px]" />
          <div className="absolute inset-0 bg-grid opacity-30" />

          <div className="relative flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#d4a574]">Popular paths</p>
              <h2 className="mt-3 text-3xl font-semibold text-[#f5f0e8]">Choose the goal that fits your life.</h2>
            </div>
            <Link href="/auth/signup">
              <button className="rounded-xl bg-gradient-to-r from-[#c4854c] to-[#e8a838] px-5 py-2.5 text-sm font-semibold text-[#f5f0e8] shadow-lg shadow-[#c4854c]/20 transition-all hover:shadow-[#c4854c]/30 hover:brightness-110">
                Start your profile
              </button>
            </Link>
          </div>

          <div className="relative mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {goals.map((goal) => (
              <div key={goal} className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4 transition-all hover:bg-white/[0.06]">
                <p className="text-lg font-medium text-[#f5f0e8]">{goal}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <footer id="about" className="flex flex-col gap-4 border-t border-white/[0.06] py-6 text-sm text-zinc-500 md:flex-row md:items-center md:justify-between">
          <p>© 2026 South Asian Fitness</p>
          <div className="flex flex-wrap gap-4">
            <Link href="/auth/login" className="transition hover:text-zinc-300">Login</Link>
            <Link href="/auth/signup" className="transition hover:text-zinc-300">Sign up</Link>
            <Link href="/privacy" className="transition hover:text-zinc-300">Privacy</Link>
            <Link href="/terms" className="transition hover:text-zinc-300">Terms</Link>
          </div>
        </footer>
      </main>
    </div>
  );
}

/* ── Benefit Card ─────────────────────────────────────────────────────── */

function BenefitCard({
  badge,
  title,
  description,
}: {
  badge: string;
  title: string;
  description: string;
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl glass p-6 transition-all duration-300 hover:shadow-[0_0_30px_rgba(16,185,129,0.05)]">
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-[#c4854c]/5 blur-[40px] transition-all duration-500 group-hover:bg-[#c4854c]/10" />
      <p className="relative text-xs font-semibold uppercase tracking-[0.2em] text-[#d4a574]">
        {badge}
      </p>
      <h2 className="relative mt-4 text-xl font-semibold text-[#f5f0e8]">{title}</h2>
      <p className="relative mt-2 text-sm text-zinc-400">{description}</p>
    </div>
  );
}
