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
        <div className="absolute bottom-0 left-1/4 h-[300px] w-[300px] rounded-full bg-stone-50 blur-[80px]" />
      </div>

      <div className="relative mx-auto max-w-5xl px-6">
        {/* Header */}
        <div className="mb-16 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-stone-900">
            Simple pricing
          </p>
          <h2 className="mt-4 font-serif text-3xl font-bold text-stone-900 md:text-5xl">
            Start free. Upgrade when you're ready.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-stone-500">
            No credit card required. No hidden fees. Upgrade to Pro when you want unlimited power.
          </p>
        </div>

        {/* Cards */}
        <div className="grid gap-6 md:grid-cols-2 md:items-start">
          {/* Free Card */}
          <div className="relative rounded-3xl border border-stone-200 bg-stone-50 p-8 transition-all duration-500 hover:bg-stone-50">
            <div className="mb-6">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-stone-500">Free</p>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-stone-900">$0</span>
                <span className="text-sm text-stone-500">/month</span>
              </div>
              <p className="mt-2 text-sm text-stone-500">
                Everything you need to start your fitness journey.
              </p>
            </div>

            <ul className="mb-8 space-y-3">
              {freeFeatures.map((f) => (
                <li key={f} className="flex items-start gap-3 text-sm text-stone-600">
                  <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-stone-100 flex items-center justify-center text-[10px] text-stone-500">
                    ✓
                  </span>
                  {f}
                </li>
              ))}
            </ul>

            <Link
              href="/auth/signup"
              className="block w-full rounded-xl border border-stone-200 bg-stone-50 py-3 text-center text-sm font-semibold text-stone-600 transition-all hover:bg-stone-50 hover:text-stone-900"
            >
              Get started free
            </Link>
          </div>

          {/* Pro Card — Visually dominant */}
          <div className="relative scale-[1.03] rounded-3xl border border-white/30 bg-gradient-to-b from-orange-500/10 to-transparent p-8 shadow-orange-500/10 transition-all duration-500 hover:shadow-orange-500/15">
            {/* Glow accent */}
            <div className="absolute -inset-px rounded-3xl bg-gradient-to-b from-orange-500/10 via-transparent to-transparent opacity-50" />

            {/* Badge */}
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <span className="rounded-full bg-gradient-to-r from-orange-500 to-orange-600 px-4 py-1 text-xs font-bold uppercase tracking-wider text-stone-900 shadow-lg ">
                Most Popular
              </span>
            </div>

            <div className="relative mb-6">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-stone-600">Pro</p>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-stone-900">$9</span>
                <span className="text-sm text-stone-500">/month</span>
              </div>
              <p className="mt-2 text-sm text-stone-600">
                Full power. Unlimited plans. Complete control.
              </p>
            </div>

            <ul className="relative mb-8 space-y-3">
              {proFeatures.map((f) => (
                <li key={f} className="flex items-start gap-3 text-sm text-stone-900">
                  <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-white/20 flex items-center justify-center text-[10px] text-stone-900">
                    ✓
                  </span>
                  {f}
                </li>
              ))}
            </ul>

            <Link
              href="/auth/signup"
              className="relative block w-full rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 py-3.5 text-center text-sm font-bold text-stone-900 shadow-lg shadow-orange-500/20 transition-all hover:shadow-orange-500/30 hover:brightness-110"
            >
              Start 14-day free trial
            </Link>
            <p className="relative mt-3 text-center text-xs text-stone-500">
              No credit card required • Cancel anytime
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
