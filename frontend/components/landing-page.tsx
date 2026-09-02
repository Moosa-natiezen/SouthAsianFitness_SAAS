"use client";

import Link from "next/link";

/* ── Data ──────────────────────────────────────────────────────────────── */

const features = [
  { title: "Your cultural cuisine", desc: "Dal, biryani, tikka, paratha — optimized, not eliminated.", icon: "🍛" },
  { title: "Precision macros", desc: "Every meal calculated to hit your exact targets.", icon: "📊" },
  { title: "AI-powered plans", desc: "Generate personalized plans in seconds, not hours.", icon: "⚡" },
  { title: "Budget-aware", desc: "Plans that fit your grocery budget and local prices.", icon: "💰" },
];

const steps = [
  { num: "01", title: "Tell us your goals", desc: "Set your calorie target, activity level, and food preferences." },
  { num: "02", title: "Get your plan", desc: "AI generates a personalized meal plan with South Asian dishes." },
  { num: "03", title: "Track & adjust", desc: "Log progress, refine your plan, and hit your targets." },
];

/* ── Landing Page ───────────────────────────────────────────────────── */

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#05050A] text-[#FAFAFA] overflow-hidden">
      {/* ── Nav ──────────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 glass">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 text-xs font-bold text-white shadow-lg shadow-indigo-500/20">
              SA
            </div>
            <span className="text-sm font-semibold text-white">South Asian Fitness</span>
          </div>
          <nav className="hidden items-center gap-6 text-sm text-zinc-400 md:flex">
            <a href="#features" className="hover:text-white transition-colors duration-300">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors duration-300">How it works</a>
            <a href="#pricing" className="hover:text-white transition-colors duration-300">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm text-zinc-400 hover:text-white transition-colors duration-300">
              Log in
            </Link>
            <Link
              href="/auth/signup"
              className="btn-chrome-accent rounded-lg px-4 py-2 text-sm"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative flex min-h-screen items-center justify-center px-6">
        {/* Hero glow orbs */}
        <div className="glow-orb-indigo absolute top-1/4 left-1/4 h-[600px] w-[600px] animate-pulse-glow" />
        <div className="glow-orb-violet absolute bottom-1/4 right-1/4 h-[500px] w-[500px] animate-pulse-glow" style={{ animationDelay: "1s" }} />
        <div className="glow-orb-rose absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[400px] w-[400px] animate-pulse-glow" style={{ animationDelay: "2s" }} />

        <div className="relative z-10 max-w-3xl text-center">
          <div className="animate-fade-in-up">
            <p className="mb-6 text-xs font-medium uppercase tracking-[0.2em] text-indigo-400/80">
              AI-powered nutrition for South Asian cuisine
            </p>
          </div>
          <div className="animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
            <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl lg:text-7xl">
              Fitness that fits{" "}
              <span className="text-gradient-accent">your culture.</span>
              <br />
              Powered by AI.
            </h1>
          </div>
          <div className="animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
            <p className="mt-6 text-lg leading-relaxed text-zinc-400 max-w-xl mx-auto">
              Generate personalized, macro-optimized South Asian meal plans in seconds.
              Stop sacrificing the food you love to hit your goals.
            </p>
          </div>
          <div className="animate-fade-in-up mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center" style={{ animationDelay: "0.3s" }}>
            <Link
              href="/onboarding"
              className="btn-chrome-accent rounded-xl px-8 py-3.5 text-sm font-semibold"
            >
              Start for free
            </Link>
            <a
              href="#how-it-works"
              className="btn-chrome rounded-xl px-8 py-3.5 text-sm font-medium text-zinc-300"
            >
              See how it works
            </a>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────── */}
      <section id="features" className="relative border-t border-white/[0.06] py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-indigo-400/80 mb-3">Features</p>
          <h2 className="text-2xl font-bold md:text-3xl mb-12">
            Everything you need to{" "}
            <span className="text-gradient-accent">eat right.</span>
          </h2>
          <div className="grid gap-5 md:grid-cols-2">
            {features.map((f, i) => (
              <div
                key={f.title}
                className="glass rounded-2xl p-6 transition-all duration-300 hover:border-indigo-500/20 hover:shadow-[0_0_30px_rgba(99,102,241,0.08)] group"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="flex items-start gap-4">
                  <span className="text-2xl mt-0.5">{f.icon}</span>
                  <div>
                    <h3 className="font-medium text-white group-hover:text-indigo-300 transition-colors duration-300">{f.title}</h3>
                    <p className="mt-1.5 text-sm text-zinc-400 leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────── */}
      <section id="how-it-works" className="relative border-t border-white/[0.06] py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-indigo-400/80 mb-3">How it works</p>
          <h2 className="text-2xl font-bold md:text-3xl mb-12">
            Three steps to your{" "}
            <span className="text-gradient-cardamom">perfect plan.</span>
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            {steps.map((s) => (
              <div key={s.num} className="glass rounded-2xl p-6 group transition-all duration-300 hover:border-violet-500/20">
                <span className="text-xs font-mono text-indigo-400/60">{s.num}</span>
                <h3 className="mt-3 font-medium text-white group-hover:text-violet-300 transition-colors duration-300">{s.title}</h3>
                <p className="mt-2 text-sm text-zinc-400 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────────────────── */}
      <section id="pricing" className="relative border-t border-white/[0.06] py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-indigo-400/80 mb-3">Pricing</p>
          <h2 className="text-2xl font-bold md:text-3xl mb-12">
            Simple, transparent{" "}
            <span className="text-gradient-saffron">pricing.</span>
          </h2>
          <div className="grid gap-6 md:grid-cols-2 max-w-2xl">
            {/* Free tier */}
            <div className="glass rounded-2xl p-8 transition-all duration-300 hover:border-white/10">
              <p className="text-sm text-zinc-400">Free</p>
              <p className="mt-2 text-3xl font-bold text-white">$0</p>
              <p className="mt-1 text-sm text-zinc-500">/month</p>
              <ul className="mt-6 space-y-3 text-sm text-zinc-400">
                <li className="flex items-center gap-2.5">
                  <span className="text-zinc-600">—</span> 3 meal plans / month
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-zinc-600">—</span> Food library access
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-zinc-600">—</span> Progress tracking
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="btn-chrome mt-8 block w-full rounded-xl py-2.5 text-center text-sm font-medium text-zinc-300"
              >
                Get started
              </Link>
            </div>
            {/* Pro tier */}
            <div className="glass rounded-2xl p-8 relative border-indigo-500/20 transition-all duration-300 hover:border-indigo-500/30 hover:shadow-[0_0_40px_rgba(99,102,241,0.1)]">
              <div className="absolute -top-3 right-6 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 px-3 py-0.5 text-xs font-semibold text-white shadow-lg shadow-indigo-500/30">
                Popular
              </div>
              <p className="text-sm text-zinc-400">Pro</p>
              <p className="mt-2 text-3xl font-bold text-gradient-accent">$9</p>
              <p className="mt-1 text-sm text-zinc-500">/month</p>
              <ul className="mt-6 space-y-3 text-sm text-zinc-400">
                <li className="flex items-center gap-2.5">
                  <span className="text-indigo-400">✓</span> Unlimited meal plans
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-indigo-400">✓</span> AI workout generator
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-indigo-400">✓</span> Saved plans archive
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-indigo-400">✓</span> Priority support
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="btn-chrome-accent mt-8 block w-full rounded-xl py-2.5 text-center text-sm font-semibold"
              >
                Start free trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="relative border-t border-white/[0.06] py-24">
        <div className="glow-orb-indigo absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[300px] w-[300px]" />
        <div className="relative z-10 mx-auto max-w-2xl px-6 text-center">
          <h2 className="text-2xl font-bold md:text-3xl">
            Your goals. Your food.{" "}
            <span className="text-gradient-accent">Your plan.</span>
          </h2>
          <p className="mt-4 text-zinc-400">
            Start building sustainable fitness habits with the food you love.
          </p>
          <Link
            href="/onboarding"
            className="btn-chrome-accent mt-8 inline-block rounded-xl px-8 py-3.5 text-sm font-semibold"
          >
            Start for free
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.06] py-8">
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
