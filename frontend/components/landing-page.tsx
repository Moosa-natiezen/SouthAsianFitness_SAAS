"use client";

import Link from "next/link";

/* ── Landing Page — Cultural Premium Aesthetic ─────────────────────── */

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden bg-[#FAF9F6]">
      {/* ── Nav ──────────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 bg-[#FAF9F6]/70 backdrop-blur-xl border-b border-stone-200/50">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#E27B38] text-xs font-bold text-white shadow-sm shadow-[#E27B38]/20">
              SA
            </div>
            <span className="text-sm font-semibold text-stone-800 tracking-tight">South Asian Fitness</span>
          </div>
          <nav className="hidden items-center gap-8 text-sm text-stone-500 md:flex">
            <a href="#features" className="hover:text-stone-900 transition-colors duration-200">Features</a>
            <a href="#how-it-works" className="hover:text-stone-900 transition-colors duration-200">How it works</a>
            <a href="#pricing" className="hover:text-stone-900 transition-colors duration-200">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm text-stone-500 hover:text-stone-900 transition-colors duration-200">
              Log in
            </Link>
            <Link
              href="/auth/signup"
              className="rounded-full bg-stone-900 px-5 py-2 text-sm font-medium text-white hover:bg-stone-800 transition-all duration-200 active:scale-[0.97]"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero — Bento Split ─────────────────────────────────────── */}
      <section className="relative pt-24 pb-12 md:pt-32 md:pb-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid items-center gap-12 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
            {/* Left — Copy & CTA */}
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center gap-2 rounded-full bg-[#E27B38]/10 px-4 py-1.5 mb-6">
                <div className="h-1.5 w-1.5 rounded-full bg-[#E27B38]" />
                <span className="text-xs font-medium text-[#E27B38] tracking-wide">AI-Powered Nutrition</span>
              </div>
              <h1 className="font-serif text-4xl font-semibold leading-[1.1] tracking-tight text-stone-900 md:text-5xl lg:text-6xl">
                The world&apos;s first South Asian nutrition AI.
              </h1>
              <p className="mt-6 text-lg leading-relaxed text-stone-500 max-w-lg mx-auto lg:mx-0">
                Track cultural macros accurately. Hit your goals without sacrificing the food you love.
                Powered by AI, built for your kitchen.
              </p>
              <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2.5 rounded-full bg-[#E27B38] px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-[#E27B38]/20 transition-all duration-200 hover:shadow-xl hover:shadow-[#E27B38]/30 hover:bg-[#C4642A] active:scale-[0.97]"
                >
                  Start for Free
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                  </svg>
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center gap-2 rounded-full border border-stone-200 px-8 py-3.5 text-sm font-medium text-stone-600 transition-all duration-200 hover:bg-stone-50 hover:border-stone-300 active:scale-[0.97]"
                >
                  See how it works
                </a>
              </div>
            </div>

            {/* Right — Floating Food Image */}
            <div className="relative flex justify-center lg:justify-end">
              {/* Soft ambient glow behind image */}
              <div className="absolute inset-0 m-auto h-[70%] w-[70%] rounded-full bg-[#E27B38]/5 blur-3xl" />
              <div className="relative w-full max-w-md">
                <div className="overflow-hidden rounded-[2.5rem] shadow-2xl shadow-stone-900/10 ring-1 ring-stone-900/5">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&h=1000&fit=crop&crop=center"
                    alt="Vibrant South Asian Chicken Tikka bowl with aromatic spices and fresh herbs"
                    className="aspect-[4/5] w-full object-cover"
                  />
                </div>
                {/* Floating stat card */}
                <div className="absolute -bottom-4 -left-4 rounded-2xl bg-white p-4 shadow-xl shadow-stone-900/5 ring-1 ring-stone-900/5">
                  <div className="text-2xl font-bold text-stone-900 font-serif">215+</div>
                  <div className="text-xs text-stone-500 mt-0.5">South Asian dishes</div>
                </div>
                {/* Floating accuracy badge */}
                <div className="absolute -top-3 -right-3 rounded-2xl bg-white p-3 shadow-xl shadow-stone-900/5 ring-1 ring-stone-900/5">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#065F46]/10">
                      <svg className="h-4 w-4 text-[#065F46]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-stone-800">Macro Accurate</div>
                      <div className="text-[10px] text-stone-400">Per serving</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Trust / Social Proof ─────────────────────────────────────── */}
      <section className="bg-stone-100/60 py-16">
        <div className="mx-auto max-w-5xl px-6 text-center">
          {/* Stars */}
          <div className="mb-4 flex justify-center gap-1">
            {[...Array(5)].map((_, i) => (
              <svg key={i} className="h-5 w-5 text-[#E27B38]" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
          <h2 className="text-2xl font-semibold text-stone-900 md:text-3xl font-serif">
            The Smartest Way to Track Cultural Cuisines.
          </h2>
          <p className="mt-3 text-stone-500">
            Trusted by 2,000+ South Asians building healthier habits.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            {/* App Store */}
            <button className="inline-flex items-center gap-3 rounded-2xl border border-stone-200 bg-white px-6 py-3 text-left transition-all duration-200 hover:shadow-md hover:border-stone-300 active:scale-[0.97]">
              <svg className="h-7 w-7 text-stone-800" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
              </svg>
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wide text-stone-400">Download on the</div>
                <div className="text-sm font-semibold text-stone-800">App Store</div>
              </div>
            </button>
            {/* Google Play */}
            <button className="inline-flex items-center gap-3 rounded-2xl border border-stone-200 bg-white px-6 py-3 text-left transition-all duration-200 hover:shadow-md hover:border-stone-300 active:scale-[0.97]">
              <svg className="h-7 w-7 text-stone-800" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3.609 1.814 13.792 12 3.61 22.186a.996.996 0 0 1-.61-.92V2.734a1 1 0 0 1 .609-.92zm10.89 10.893 2.302 2.302-10.937 6.333 8.635-8.635zm3.199-1.707 2.173 1.262a1.001 1.001 0 0 1 0 1.74l-2.173 1.262-2.535-2.535 2.535-2.729zM5.864 2.658 16.8 8.99l-2.302 2.302-8.634-8.634z" />
              </svg>
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wide text-stone-400">Get it on</div>
                <div className="text-sm font-semibold text-stone-800">Google Play</div>
              </div>
            </button>
          </div>
        </div>
      </section>

      {/* ── Feature Blocks ──────────────────────────────────────────── */}
      <section id="features" className="bg-[#FAF9F6] py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-20 text-center">
            <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-[#E27B38]">Features</p>
            <h2 className="text-3xl font-semibold tracking-tight text-stone-900 md:text-4xl font-serif">
              Nutrition tracking made effortless for our food.
            </h2>
            <p className="mt-4 text-lg text-stone-500 max-w-xl mx-auto">
              Built specifically for South Asian cuisine — not a generic Western diet app.
            </p>
          </div>

          {/* Feature 1 — AI Coach (Image Left, Text Right) */}
          <div id="how-it-works" className="mb-16">
            <div className="glass-warm rounded-3xl p-8 md:p-12 lg:p-16">
              <div className="flex flex-col items-center gap-12 lg:flex-row lg:gap-20">
                {/* Phone Mockup */}
                <div className="flex-shrink-0">
                  <div className="relative mx-auto w-60 overflow-hidden rounded-[2.5rem] border-[3px] border-stone-200/80 bg-white shadow-xl shadow-stone-900/5">
                    {/* Notch */}
                    <div className="absolute inset-x-0 top-0 z-10 flex justify-center pt-1">
                      <div className="h-5 w-20 rounded-b-2xl bg-stone-900" />
                    </div>
                    {/* Screen content */}
                    <div className="aspect-[9/16] bg-gradient-to-b from-[#E27B38]/5 to-white p-4 pt-10">
                      <div className="mb-3 rounded-xl bg-[#E27B38] px-3 py-2 text-xs font-semibold text-white text-center">
                        AI Workout Streaming
                      </div>
                      <div className="space-y-2">
                        {[
                          { name: "Barbell Squat", detail: "4 × 8 @ 185lb" },
                          { name: "Romanian Deadlift", detail: "3 × 10 @ 155lb" },
                          { name: "Walking Lunges", detail: "3 × 12 @ 40lb" },
                        ].map((ex) => (
                          <div key={ex.name} className="rounded-xl bg-stone-50 border border-stone-100 p-2.5">
                            <div className="text-xs font-semibold text-stone-800">{ex.name}</div>
                            <div className="text-[10px] text-stone-400 mt-0.5">{ex.detail}</div>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 flex items-center gap-1.5">
                        <div className="h-1.5 w-1.5 rounded-full bg-[#E27B38] animate-pulse" />
                        <span className="text-[10px] font-medium text-[#E27B38]">Generating your routine...</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Text */}
                <div className="max-w-md text-center lg:text-left">
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#E27B38]/10 text-xl">
                    🏋️
                  </div>
                  <h3 className="text-2xl font-semibold text-stone-900 font-serif">
                    Get a coach in your corner
                  </h3>
                  <p className="mt-4 text-base leading-relaxed text-stone-500">
                    Our AI workout streaming engine builds personalized routines in real-time.
                    Every set, rep, and rest interval is tailored to your goals and experience level.
                  </p>
                  <Link
                    href="/onboarding"
                    className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#E27B38] hover:text-[#C4642A] transition-colors"
                  >
                    Get started free
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                    </svg>
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 2 — Food Library (Text Left, Image Right) */}
          <div>
            <div className="glass-warm rounded-3xl p-8 md:p-12 lg:p-16">
              <div className="flex flex-col items-center gap-12 lg:flex-row-reverse lg:gap-20">
                {/* Phone Mockup */}
                <div className="flex-shrink-0">
                  <div className="relative mx-auto w-60 overflow-hidden rounded-[2.5rem] border-[3px] border-stone-200/80 bg-white shadow-xl shadow-stone-900/5">
                    {/* Notch */}
                    <div className="absolute inset-x-0 top-0 z-10 flex justify-center pt-1">
                      <div className="h-5 w-20 rounded-b-2xl bg-stone-900" />
                    </div>
                    {/* Screen content */}
                    <div className="aspect-[9/16] bg-gradient-to-b from-[#065F46]/5 to-white p-4 pt-10">
                      <div className="mb-3 rounded-xl bg-[#065F46] px-3 py-2 text-xs font-semibold text-white text-center">
                        Food Library
                      </div>
                      <div className="mb-2 rounded-xl bg-stone-50 border border-stone-100 p-2.5">
                        <div className="text-xs font-semibold text-stone-800">🍛 Chicken Biryani</div>
                        <div className="mt-1 flex gap-1.5">
                          <span className="rounded-full bg-[#E27B38]/10 px-2 py-0.5 text-[9px] font-medium text-[#E27B38]">520 cal</span>
                          <span className="rounded-full bg-[#0891B2]/10 px-2 py-0.5 text-[9px] font-medium text-[#0891B2]">32g P</span>
                        </div>
                      </div>
                      <div className="mb-2 rounded-xl bg-stone-50 border border-stone-100 p-2.5">
                        <div className="text-xs font-semibold text-stone-800">🥘 Daal Chawal</div>
                        <div className="mt-1 flex gap-1.5">
                          <span className="rounded-full bg-[#E27B38]/10 px-2 py-0.5 text-[9px] font-medium text-[#E27B38]">420 cal</span>
                          <span className="rounded-full bg-[#0891B2]/10 px-2 py-0.5 text-[9px] font-medium text-[#0891B2]">20g P</span>
                        </div>
                      </div>
                      <div className="mb-2 rounded-xl bg-stone-50 border border-stone-100 p-2.5">
                        <div className="text-xs font-semibold text-stone-800">🫓 Garlic Naan</div>
                        <div className="mt-1 flex gap-1.5">
                          <span className="rounded-full bg-[#E27B38]/10 px-2 py-0.5 text-[9px] font-medium text-[#E27B38]">260 cal</span>
                          <span className="rounded-full bg-[#0891B2]/10 px-2 py-0.5 text-[9px] font-medium text-[#0891B2]">7g P</span>
                        </div>
                      </div>
                      <div className="text-center text-[10px] text-stone-400 mt-1">215+ South Asian dishes</div>
                    </div>
                  </div>
                </div>

                {/* Text */}
                <div className="max-w-md text-center lg:text-left">
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#065F46]/10 text-xl">
                    🍛
                  </div>
                  <h3 className="text-2xl font-semibold text-stone-900 font-serif">
                    Log Biryani without the guesswork
                  </h3>
                  <p className="mt-4 text-base leading-relaxed text-stone-500">
                    Over 215+ South Asian dishes pre-loaded with accurate macros.
                    From Butter Chicken to Gulab Jamun — search, log, and track in seconds.
                  </p>
                  <Link
                    href="/onboarding"
                    className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#065F46] hover:text-[#047857] transition-colors"
                  >
                    Explore food library
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                    </svg>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────────────────── */}
      <section id="pricing" className="bg-stone-100/40 py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-[#E27B38]">Pricing</p>
            <h2 className="text-3xl font-semibold tracking-tight text-stone-900 md:text-4xl font-serif">
              Simple, transparent pricing.
            </h2>
            <p className="mt-3 text-stone-500">Start free. Upgrade when you&apos;re ready.</p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 max-w-2xl mx-auto">
            {/* Free tier */}
            <div className="rounded-3xl border border-stone-200 bg-white p-8 shadow-sm transition-all duration-300 hover:shadow-md">
              <p className="text-sm font-medium text-stone-400">Free</p>
              <p className="mt-2 text-4xl font-bold text-stone-900 font-serif">$0</p>
              <p className="mt-1 text-sm text-stone-400">forever</p>
              <ul className="mt-6 space-y-3.5 text-sm text-stone-600">
                <li className="flex items-center gap-3">
                  <span className="text-stone-300">—</span> 3 meal plans / month
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-stone-300">—</span> Food library (215+ dishes)
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-stone-300">—</span> Progress tracking
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-full border border-stone-200 py-3 text-center text-sm font-medium text-stone-700 transition-all duration-200 hover:bg-stone-50 hover:border-stone-300 active:scale-[0.97]"
              >
                Get started
              </Link>
            </div>
            {/* Pro tier */}
            <div className="relative rounded-3xl border-2 border-[#E27B38] bg-white p-8 shadow-lg shadow-[#E27B38]/5 transition-all duration-300 hover:shadow-xl hover:shadow-[#E27B38]/10">
              <div className="absolute -top-3.5 right-6 rounded-full bg-[#E27B38] px-3 py-1 text-xs font-semibold text-white shadow-md shadow-[#E27B38]/20">
                Most Popular
              </div>
              <p className="text-sm font-medium text-stone-400">Pro</p>
              <p className="mt-2 text-4xl font-bold text-stone-900 font-serif">$9</p>
              <p className="mt-1 text-sm text-stone-400">/month</p>
              <ul className="mt-6 space-y-3.5 text-sm text-stone-600">
                <li className="flex items-center gap-3">
                  <span className="text-[#E27B38] font-bold">✓</span> Unlimited meal plans
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-[#E27B38] font-bold">✓</span> AI workout generator
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-[#E27B38] font-bold">✓</span> Saved plans archive
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-[#E27B38] font-bold">✓</span> Priority support
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-full bg-[#E27B38] py-3 text-center text-sm font-semibold text-white shadow-md shadow-[#E27B38]/20 transition-all duration-200 hover:bg-[#C4642A] hover:shadow-lg active:scale-[0.97]"
              >
                Start free trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA ──────────────────────────────────────────────── */}
      <section className="bg-[#065F46] py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-semibold text-white md:text-4xl font-serif">
            Your goals. Your food. Your plan.
          </h2>
          <p className="mt-4 text-emerald-100/80 text-lg">
            Start building sustainable fitness habits with the food you love.
          </p>
          <Link
            href="/onboarding"
            className="mt-8 inline-flex items-center gap-2.5 rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-[#065F46] shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-[1.02] active:scale-[0.97]"
          >
            Start for free
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="bg-stone-900 py-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 text-sm text-stone-400 md:flex-row md:items-center md:justify-between">
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
