"use client";

import Link from "next/link";

const freeFeatures = [
  "3 AI meal plans per month",
  "Basic macro tracking",
  "South Asian food database (198+ foods)",
  "Weight progress logging",
  "Community support",
];

const proFeatures = [
  "Unlimited AI meal plan generations",
  "Custom macro targets (protein, carbs, fat)",
  "Advanced meal plan optimizer",
  "3D gamified dashboard",
  "Detailed nutrition analytics",
  "Budget-aware meal planning",
  "Priority support",
  "Early access to new features",
];

/**
 * PricingSection — Two pricing cards with the Pro card visually dominant.
 * Designed for maximum conversion with glow effects, scale emphasis, and
 * clear CTA that pushes users into the signup/onboarding pipeline.
 */
export function PricingSection() {
  return (
    <section className="relative py-24 md:py-32">
      {/* Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute right-1/4 top-0 h-[400px] w-[400px] rounded-full bg-zinc-700/5 blur-[100px]" />
        <div className="absolute bottom-0 left-1/4 h-[300px] w-[300px] rounded-full bg-white/[0.05] blur-[80px]" />
      </div>

      <div className="relative mx-auto max-w-5xl px-6">
        {/* Header */}
        <div className="mb-16 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-white">
            Simple pricing
          </p>
          <h2 className="mt-4 font-serif text-3xl font-bold text-white md:text-5xl">
            Start free. Upgrade when you're ready.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-zinc-400">
            No credit card required. No hidden fees. Upgrade to Pro when you want unlimited power.
          </p>
        </div>

        {/* Cards */}
        <div className="grid gap-6 md:grid-cols-2 md:items-start">
          {/* Free Card */}
          <div className="relative rounded-3xl border border-white/10 bg-white/[0.04] p-8 transition-all duration-500 hover:bg-white/[0.05]">
            <div className="mb-6">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-zinc-400">Free</p>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-white">$0</span>
                <span className="text-sm text-zinc-400">/month</span>
              </div>
              <p className="mt-2 text-sm text-zinc-400">
                Everything you need to start your fitness journey.
              </p>
            </div>

            <ul className="mb-8 space-y-3">
              {freeFeatures.map((f) => (
                <li key={f} className="flex items-start gap-3 text-sm text-zinc-300">
                  <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-white/[0.06] flex items-center justify-center text-[10px] text-zinc-400">
                    ✓
                  </span>
                  {f}
                </li>
              ))}
            </ul>

            <Link
              href="/auth/signup"
              className="block w-full rounded-xl border border-white/10 bg-white/[0.05] py-3 text-center text-sm font-semibold text-zinc-300 transition-all hover:bg-white/[0.08] hover:text-white"
            >
              Get started free
            </Link>
          </div>

          {/* Pro Card — Visually dominant */}
          <div className="relative scale-[1.03] rounded-3xl border border-white/30 bg-gradient-to-b from-zinc-700/10 to-transparent p-8 shadow-[0_0_60px_rgba(220,20,60,0.1)] transition-all duration-500 hover:shadow-[0_0_80px_rgba(220,20,60,0.15)]">
            {/* Glow accent */}
            <div className="absolute -inset-px rounded-3xl bg-gradient-to-b from-zinc-700/20 via-transparent to-transparent opacity-50" />

            {/* Badge */}
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <span className="rounded-full bg-gradient-to-r from-zinc-700 to-zinc-800 px-4 py-1 text-xs font-bold uppercase tracking-wider text-white shadow-lg ">
                Most Popular
              </span>
            </div>

            <div className="relative mb-6">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-zinc-300">Pro</p>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-white">$9</span>
                <span className="text-sm text-zinc-400">/month</span>
              </div>
              <p className="mt-2 text-sm text-zinc-300">
                Full power. Unlimited plans. Complete control.
              </p>
            </div>

            <ul className="relative mb-8 space-y-3">
              {proFeatures.map((f) => (
                <li key={f} className="flex items-start gap-3 text-sm text-zinc-100">
                  <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-white/20 flex items-center justify-center text-[10px] text-white">
                    ✓
                  </span>
                  {f}
                </li>
              ))}
            </ul>

            <Link
              href="/auth/signup"
              className="relative block w-full rounded-xl bg-gradient-to-r from-zinc-700 to-zinc-800 py-3.5 text-center text-sm font-bold text-white shadow-lg shadow-[#DC143C]/25 transition-all hover:shadow-[#DC143C]/40 hover:brightness-110"
            >
              Start 14-day free trial
            </Link>
            <p className="relative mt-3 text-center text-xs text-zinc-400">
              No credit card required • Cancel anytime
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
