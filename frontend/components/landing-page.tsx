"use client";

import Link from "next/link";

/* ── Data ──────────────────────────────────────────────────────────────── */

const features = [
  { title: "Your cultural cuisine", desc: "Dal, biryani, tikka, paratha — optimized, not eliminated." },
  { title: "Precision macros", desc: "Every meal calculated to hit your exact targets." },
  { title: "AI-powered plans", desc: "Generate personalized plans in seconds, not hours." },
  { title: "Budget-aware", desc: "Plans that fit your grocery budget and local prices." },
];

const steps = [
  { num: "01", title: "Tell us your goals", desc: "Set your calorie target, activity level, and food preferences." },
  { num: "02", title: "Get your plan", desc: "AI generates a personalized meal plan with South Asian dishes." },
  { num: "03", title: "Track & adjust", desc: "Log progress, refine your plan, and hit your targets." },
];

/* ── Landing Page ───────────────────────────────────────────────────── */

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#09090b] text-[#fafafa]">
      {/* ── Nav ──────────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/8 bg-[#09090b]/80 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-xs font-bold text-[#09090b]">
              SA
            </div>
            <span className="text-sm font-semibold">South Asian Fitness</span>
          </div>
          <nav className="hidden items-center gap-6 text-sm text-zinc-400 md:flex">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm text-zinc-400 hover:text-white transition-colors">
              Log in
            </Link>
            <Link
              href="/auth/signup"
              className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-[#09090b] hover:bg-zinc-200 transition-colors"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="flex min-h-screen items-center justify-center px-6">
        <div className="max-w-2xl text-center">
          <p className="mb-6 text-xs font-medium uppercase tracking-widest text-zinc-500">
            AI-powered nutrition for South Asian cuisine
          </p>
          <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl lg:text-7xl">
            Fitness that fits{" "}
            <span className="text-zinc-400">your culture.</span>
            <br />
            Powered by AI.
          </h1>
          <p className="mt-6 text-lg leading-relaxed text-zinc-400">
            Generate personalized, macro-optimized South Asian meal plans in seconds.
            Stop sacrificing the food you love to hit your goals.
          </p>
          <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/onboarding"
              className="rounded-lg bg-white px-6 py-3 text-sm font-medium text-[#09090b] hover:bg-zinc-200 transition-colors"
            >
              Start for free
            </Link>
            <a
              href="#how-it-works"
              className="rounded-lg border border-white/10 px-6 py-3 text-sm font-medium text-zinc-400 hover:text-white hover:border-white/20 transition-colors"
            >
              See how it works
            </a>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────── */}
      <section id="features" className="border-t border-white/8 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500 mb-3">Features</p>
          <h2 className="text-2xl font-bold md:text-3xl mb-12">
            Everything you need to eat right.
          </h2>
          <div className="grid gap-6 md:grid-cols-2">
            {features.map((f) => (
              <div key={f.title} className="rounded-xl border border-white/8 bg-[#18181b] p-6">
                <h3 className="font-medium text-[#fafafa]">{f.title}</h3>
                <p className="mt-1.5 text-sm text-zinc-400">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────── */}
      <section id="how-it-works" className="border-t border-white/8 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500 mb-3">How it works</p>
          <h2 className="text-2xl font-bold md:text-3xl mb-12">
            Three steps to your perfect plan.
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            {steps.map((s) => (
              <div key={s.num}>
                <span className="text-xs font-mono text-zinc-600">{s.num}</span>
                <h3 className="mt-2 font-medium">{s.title}</h3>
                <p className="mt-1.5 text-sm text-zinc-400">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────────────────── */}
      <section id="pricing" className="border-t border-white/8 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500 mb-3">Pricing</p>
          <h2 className="text-2xl font-bold md:text-3xl mb-12">
            Simple, transparent pricing.
          </h2>
          <div className="grid gap-6 md:grid-cols-2 max-w-2xl">
            <div className="rounded-xl border border-white/8 bg-[#18181b] p-8">
              <p className="text-sm text-zinc-400">Free</p>
              <p className="mt-2 text-3xl font-bold">$0</p>
              <p className="mt-1 text-sm text-zinc-500">/month</p>
              <ul className="mt-6 space-y-3 text-sm text-zinc-400">
                <li className="flex items-center gap-2"><span className="text-zinc-600">—</span> 3 meal plans / month</li>
                <li className="flex items-center gap-2"><span className="text-zinc-600">—</span> Food library access</li>
                <li className="flex items-center gap-2"><span className="text-zinc-600">—</span> Progress tracking</li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-lg border border-white/10 py-2.5 text-center text-sm font-medium text-zinc-400 hover:text-white hover:border-white/20 transition-colors"
              >
                Get started
              </Link>
            </div>
            <div className="rounded-xl border border-white/20 bg-[#18181b] p-8 relative">
              <p className="absolute -top-3 right-6 rounded-full bg-white px-3 py-0.5 text-xs font-medium text-[#09090b]">
                Popular
              </p>
              <p className="text-sm text-zinc-400">Pro</p>
              <p className="mt-2 text-3xl font-bold">$9</p>
              <p className="mt-1 text-sm text-zinc-500">/month</p>
              <ul className="mt-6 space-y-3 text-sm text-zinc-400">
                <li className="flex items-center gap-2"><span className="text-white">✓</span> Unlimited meal plans</li>
                <li className="flex items-center gap-2"><span className="text-white">✓</span> AI workout generator</li>
                <li className="flex items-center gap-2"><span className="text-white">✓</span> Saved plans archive</li>
                <li className="flex items-center gap-2"><span className="text-white">✓</span> Priority support</li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-lg bg-white py-2.5 text-center text-sm font-medium text-[#09090b] hover:bg-zinc-200 transition-colors"
              >
                Start free trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="border-t border-white/8 py-24">
        <div className="mx-auto max-w-2xl px-6 text-center">
          <h2 className="text-2xl font-bold md:text-3xl">
            Your goals. Your food. Your plan.
          </h2>
          <p className="mt-4 text-zinc-400">
            Start building sustainable fitness habits with the food you love.
          </p>
          <Link
            href="/onboarding"
            className="mt-8 inline-block rounded-lg bg-white px-8 py-3 text-sm font-medium text-[#09090b] hover:bg-zinc-200 transition-colors"
          >
            Start for free
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-white/8 py-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 text-sm text-zinc-500 md:flex-row md:items-center md:justify-between">
          <p>© 2026 South Asian Fitness.</p>
          <div className="flex gap-6">
            <Link href="/auth/login" className="hover:text-zinc-300 transition-colors">Login</Link>
            <Link href="/privacy" className="hover:text-zinc-300 transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-zinc-300 transition-colors">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
