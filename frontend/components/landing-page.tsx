"use client";

import Link from "next/link";

/* ── Data ──────────────────────────────────────────────────────────────── */

const features = [
  {
    title: "Get a coach in your corner",
    desc: "Our AI workout streaming engine builds personalized routines in real-time. Every set, rep, and rest interval is tailored to your goals and experience level.",
    icon: "🏋️",
    iconBg: "bg-blue-600",
  },
  {
    title: "Log Biryani without the guesswork",
    desc: "Over 215+ South Asian dishes pre-loaded with accurate macros. From Butter Chicken to Gulab Jamun — search, log, and track in seconds.",
    icon: "🍛",
    iconBg: "bg-emerald-600",
  },
];

/* ── Landing Page ───────────────────────────────────────────────────── */

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden">
      {/* ── Nav ──────────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-200/60">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white">
              SA
            </div>
            <span className="text-sm font-semibold text-slate-900">South Asian Fitness</span>
          </div>
          <nav className="hidden items-center gap-6 text-sm text-slate-500 md:flex">
            <a href="#features" className="hover:text-slate-900 transition-colors duration-200">Features</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors duration-200">How it works</a>
            <a href="#pricing" className="hover:text-slate-900 transition-colors duration-200">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm text-slate-500 hover:text-slate-900 transition-colors duration-200">
              Log in
            </Link>
            <Link
              href="/auth/signup"
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 transition-all duration-200 active:scale-[0.97]"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Split Hero ─────────────────────────────────────────────── */}
      <section className="relative pt-20">
        <div className="grid lg:grid-cols-2 min-h-[calc(100vh-5rem)]">
          {/* Left — Copy & CTA */}
          <div className="flex items-center justify-center bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 px-8 py-16 lg:py-0">
            <div className="max-w-lg text-center lg:text-left">
              <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-white md:text-5xl lg:text-6xl">
                The world&apos;s first South Asian nutrition AI.
              </h1>
              <p className="mt-6 text-lg leading-relaxed text-blue-100/90">
                Track cultural macros accurately. Hit your goals without sacrificing the food you love.
                Powered by AI, built for your kitchen.
              </p>
              <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2 rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-blue-700 shadow-lg shadow-blue-900/30 transition-all duration-200 hover:shadow-xl hover:shadow-blue-900/40 hover:scale-[1.02] active:scale-[0.97]"
                >
                  Start for Free
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                  </svg>
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center gap-2 rounded-full border border-white/30 px-8 py-3.5 text-sm font-medium text-white transition-all duration-200 hover:bg-white/10 active:scale-[0.97]"
                >
                  See how it works
                </a>
              </div>
            </div>
          </div>

          {/* Right — Visual */}
          <div className="relative min-h-[300px] lg:min-h-0">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=1200&h=800&fit=crop&crop=center"
              alt="Delicious South Asian Chicken Tikka bowl with vibrant spices and fresh herbs"
              className="absolute inset-0 h-full w-full object-cover"
            />
            {/* Subtle gradient overlay for polish */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-700/20 to-transparent lg:bg-gradient-to-l" />
          </div>
        </div>
      </section>

      {/* ── Trust / Social Proof Banner ──────────────────────────────── */}
      <section className="bg-slate-900 py-16">
        <div className="mx-auto max-w-5xl px-6 text-center">
          {/* Stars */}
          <div className="mb-4 flex justify-center gap-1.5">
            {[...Array(5)].map((_, i) => (
              <svg key={i} className="h-6 w-6 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
          <h2 className="text-2xl font-bold text-white md:text-3xl">
            The Smartest Way to Track Cultural Cuisines.
          </h2>
          <p className="mt-3 text-slate-400">
            Trusted by 2,000+ South Asians building healthier habits.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            {/* App Store button */}
            <button className="inline-flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-800 px-6 py-3 text-left transition-all duration-200 hover:bg-slate-750 hover:border-slate-600 active:scale-[0.97]">
              <svg className="h-8 w-8 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
              </svg>
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wide text-slate-400">Download on the</div>
                <div className="text-sm font-semibold text-white">App Store</div>
              </div>
            </button>
            {/* Google Play button */}
            <button className="inline-flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-800 px-6 py-3 text-left transition-all duration-200 hover:bg-slate-750 hover:border-slate-600 active:scale-[0.97]">
              <svg className="h-8 w-8 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3.609 1.814 13.792 12 3.61 22.186a.996.996 0 0 1-.61-.92V2.734a1 1 0 0 1 .609-.92zm10.89 10.893 2.302 2.302-10.937 6.333 8.635-8.635zm3.199-1.707 2.173 1.262a1.001 1.001 0 0 1 0 1.74l-2.173 1.262-2.535-2.535 2.535-2.729zM5.864 2.658 16.8 8.99l-2.302 2.302-8.634-8.634z" />
              </svg>
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wide text-slate-400">Get it on</div>
                <div className="text-sm font-semibold text-white">Google Play</div>
              </div>
            </button>
          </div>
        </div>
      </section>

      {/* ── Alternating Feature Blocks ──────────────────────────────── */}
      <section id="features" className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
              Nutrition tracking made effortless for our food.
            </h2>
            <p className="mt-4 text-lg text-slate-500">
              Built specifically for South Asian cuisine — not a generic Western diet app.
            </p>
          </div>

          {/* Feature Block 1 — AI Coach (Image Left, Text Right) */}
          <div className="mb-20 flex flex-col items-center gap-12 rounded-3xl bg-slate-50 p-8 md:p-12 lg:flex-row lg:gap-16">
            {/* Phone Mockup */}
            <div className="flex-shrink-0">
              <div className="relative mx-auto w-64 overflow-hidden rounded-[2.5rem] border-4 border-slate-200 bg-white shadow-2xl shadow-slate-200/60">
                {/* Notch */}
                <div className="absolute inset-x-0 top-0 z-10 flex justify-center pt-1">
                  <div className="h-5 w-20 rounded-b-2xl bg-slate-900" />
                </div>
                {/* Screen content */}
                <div className="aspect-[9/16] bg-gradient-to-b from-blue-50 to-white p-4 pt-10">
                  <div className="mb-3 rounded-xl bg-blue-600 px-3 py-2 text-xs font-semibold text-white text-center">
                    AI Workout Streaming
                  </div>
                  <div className="space-y-2">
                    {[
                      { name: "Barbell Squat", detail: "4 × 8 @ 185lb" },
                      { name: "Romanian Deadlift", detail: "3 × 10 @ 155lb" },
                      { name: "Walking Lunges", detail: "3 × 12 @ 40lb" },
                    ].map((ex) => (
                      <div key={ex.name} className="rounded-lg bg-white border border-slate-100 p-2.5 shadow-sm">
                        <div className="text-xs font-semibold text-slate-800">{ex.name}</div>
                        <div className="text-[10px] text-slate-500">{ex.detail}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex items-center gap-1.5">
                    <div className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse" />
                    <span className="text-[10px] font-medium text-blue-600">Generating your routine...</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Text */}
            <div className="max-w-md text-center lg:text-left">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 text-xl">
                {features[0].icon}
              </div>
              <h3 className="text-2xl font-bold text-slate-900">
                {features[0].title}
              </h3>
              <p className="mt-4 text-base leading-relaxed text-slate-500">
                {features[0].desc}
              </p>
              <Link
                href="/onboarding"
                className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors"
              >
                Get started free
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Feature Block 2 — Accurate Logging (Text Left, Image Right) */}
          <div className="flex flex-col items-center gap-12 rounded-3xl bg-slate-50 p-8 md:p-12 lg:flex-row-reverse lg:gap-16">
            {/* Phone Mockup */}
            <div className="flex-shrink-0">
              <div className="relative mx-auto w-64 overflow-hidden rounded-[2.5rem] border-4 border-slate-200 bg-white shadow-2xl shadow-slate-200/60">
                {/* Notch */}
                <div className="absolute inset-x-0 top-0 z-10 flex justify-center pt-1">
                  <div className="h-5 w-20 rounded-b-2xl bg-slate-900" />
                </div>
                {/* Screen content */}
                <div className="aspect-[9/16] bg-gradient-to-b from-emerald-50 to-white p-4 pt-10">
                  <div className="mb-3 rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white text-center">
                    Food Library
                  </div>
                  <div className="mb-2 rounded-lg bg-white border border-slate-100 p-2 shadow-sm">
                    <div className="text-xs font-semibold text-slate-800">🍛 Chicken Biryani</div>
                    <div className="mt-1 flex gap-1.5">
                      <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[9px] font-medium text-orange-700">520 cal</span>
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[9px] font-medium text-blue-700">32g P</span>
                    </div>
                  </div>
                  <div className="mb-2 rounded-lg bg-white border border-slate-100 p-2 shadow-sm">
                    <div className="text-xs font-semibold text-slate-800">🥘 Daal Chawal</div>
                    <div className="mt-1 flex gap-1.5">
                      <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[9px] font-medium text-orange-700">420 cal</span>
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[9px] font-medium text-blue-700">20g P</span>
                    </div>
                  </div>
                  <div className="mb-2 rounded-lg bg-white border border-slate-100 p-2 shadow-sm">
                    <div className="text-xs font-semibold text-slate-800">🫓 Garlic Naan</div>
                    <div className="mt-1 flex gap-1.5">
                      <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[9px] font-medium text-orange-700">260 cal</span>
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[9px] font-medium text-blue-700">7g P</span>
                    </div>
                  </div>
                  <div className="text-center text-[10px] text-slate-400 mt-1">215+ South Asian dishes</div>
                </div>
              </div>
            </div>

            {/* Text */}
            <div className="max-w-md text-center lg:text-left">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-xl">
                {features[1].icon}
              </div>
              <h3 className="text-2xl font-bold text-slate-900">
                {features[1].title}
              </h3>
              <p className="mt-4 text-base leading-relaxed text-slate-500">
                {features[1].desc}
              </p>
              <Link
                href="/onboarding"
                className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-emerald-600 hover:text-emerald-700 transition-colors"
              >
                Explore food library
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────────────────── */}
      <section id="pricing" className="bg-slate-50 py-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
              Simple, transparent pricing.
            </h2>
            <p className="mt-3 text-slate-500">Start free. Upgrade when you&apos;re ready.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 max-w-2xl mx-auto">
            {/* Free tier */}
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm transition-all duration-200 hover:shadow-md">
              <p className="text-sm font-medium text-slate-500">Free</p>
              <p className="mt-2 text-4xl font-bold text-slate-900">$0</p>
              <p className="mt-1 text-sm text-slate-400">forever</p>
              <ul className="mt-6 space-y-3 text-sm text-slate-600">
                <li className="flex items-center gap-2.5">
                  <span className="text-slate-400">—</span> 3 meal plans / month
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-slate-400">—</span> Food library (215+ dishes)
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-slate-400">—</span> Progress tracking
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-xl border border-slate-200 py-2.5 text-center text-sm font-medium text-slate-700 transition-all duration-200 hover:bg-slate-50 active:scale-[0.97]"
              >
                Get started
              </Link>
            </div>
            {/* Pro tier */}
            <div className="relative rounded-2xl border-2 border-blue-600 bg-white p-8 shadow-lg shadow-blue-100 transition-all duration-200 hover:shadow-xl">
              <div className="absolute -top-3 right-6 rounded-full bg-blue-600 px-3 py-0.5 text-xs font-semibold text-white shadow-md">
                Most Popular
              </div>
              <p className="text-sm font-medium text-slate-500">Pro</p>
              <p className="mt-2 text-4xl font-bold text-slate-900">$9</p>
              <p className="mt-1 text-sm text-slate-400">/month</p>
              <ul className="mt-6 space-y-3 text-sm text-slate-600">
                <li className="flex items-center gap-2.5">
                  <span className="text-blue-600 font-bold">✓</span> Unlimited meal plans
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-blue-600 font-bold">✓</span> AI workout generator
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-blue-600 font-bold">✓</span> Saved plans archive
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="text-blue-600 font-bold">✓</span> Priority support
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-xl bg-blue-600 py-2.5 text-center text-sm font-semibold text-white shadow-md shadow-blue-200 transition-all duration-200 hover:bg-blue-700 hover:shadow-lg active:scale-[0.97]"
              >
                Start free trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA ──────────────────────────────────────────────── */}
      <section className="bg-blue-600 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold text-white md:text-4xl">
            Your goals. Your food. Your plan.
          </h2>
          <p className="mt-4 text-blue-100 text-lg">
            Start building sustainable fitness habits with the food you love.
          </p>
          <Link
            href="/onboarding"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-blue-700 shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-[1.02] active:scale-[0.97]"
          >
            Start for free
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="bg-slate-900 py-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 text-sm text-slate-400 md:flex-row md:items-center md:justify-between">
          <p>© 2026 South Asian Fitness.</p>
          <div className="flex gap-6">
            <Link href="/auth/login" className="hover:text-white transition-colors">Login</Link>
            <Link href="/privacy" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-white transition-colors">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
