"use client";

import Link from "next/link";

/* ── Landing Page — Warm Light Mode + Dark Contrast Sections ─────────── */

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden bg-background">
      {/* ── Nav ──────────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-stone-200 dark:border-zinc-700/50">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-600 text-xs font-bold text-stone-900 dark:text-zinc-100 shadow-sm shadow-emerald-600/20">
              SA
            </div>
            <span className="text-sm font-semibold text-stone-800 dark:text-zinc-200 tracking-tight">South Asian Fitness</span>
          </div>
          <nav className="hidden items-center gap-8 text-sm text-stone-500 dark:text-zinc-500 md:flex">
            <a href="#features" className="hover:text-stone-900 dark:text-zinc-100 transition-colors duration-200">Features</a>
            <a href="#how-it-works" className="hover:text-stone-900 dark:text-zinc-100 transition-colors duration-200">How it works</a>
            <a href="#pricing" className="hover:text-stone-900 dark:text-zinc-100 transition-colors duration-200">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/auth/login" className="text-sm text-stone-500 dark:text-zinc-500 hover:text-stone-900 dark:text-zinc-100 transition-colors duration-200">
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

      {/* ── Hero — Warm Light ─────────────────────────────────────── */}
      <section className="relative pt-24 pb-12 md:pt-32 md:pb-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid items-center gap-12 lg:grid-cols-[1.15fr_1fr] lg:gap-16">
            {/* Left — Copy & CTA */}
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-600/8 px-4 py-1.5 mb-6">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                <span className="text-xs font-medium text-emerald-600 tracking-wide">AI-Powered Nutrition</span>
              </div>
              <h1 className="font-serif text-4xl font-semibold leading-[1.08] tracking-tight text-stone-900 dark:text-zinc-100 md:text-5xl lg:text-[3.5rem]">
                Track Biryani.{" "}
                <span className="text-emerald-600">Not just calories.</span>
              </h1>
              <p className="mt-6 text-lg leading-relaxed text-stone-500 dark:text-zinc-500 max-w-lg mx-auto lg:mx-0">
                The first nutrition app built for South Asian food. 215+ cultural dishes
                with precise macros — powered by AI, designed for your kitchen.
              </p>
              <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
                <Link
                  href="/onboarding"
                  className="inline-flex items-center gap-2.5 rounded-full bg-emerald-600 px-8 py-3.5 text-sm font-semibold text-stone-900 dark:text-zinc-100 shadow-lg shadow-emerald-600/20 transition-all duration-200 hover:shadow-xl hover:shadow-emerald-600/30 hover:bg-emerald-700 active:scale-[0.97]"
                >
                  Start Tracking Free
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                  </svg>
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center gap-2 rounded-full border border-stone-200 dark:border-zinc-700 px-8 py-3.5 text-sm font-medium text-stone-600 dark:text-zinc-400 transition-all duration-200 hover:bg-stone-50 dark:bg-zinc-800 hover:border-stone-300 active:scale-[0.97]"
                >
                  See how it works
                </a>
              </div>
            </div>

            {/* Right — Floating Macro Data Card + Hero Food Image */}
            <div className="relative flex justify-center lg:justify-end">
              <div className="absolute inset-0 m-auto h-[60%] w-[60%] rounded-full bg-emerald-600/4 blur-3xl" />
              <div className="relative w-full max-w-md">
                {/* Main macro card */}
                <div className="rounded-[2rem] bg-white dark:bg-zinc-900 p-6 shadow-[0_20px_50px_rgba(0,0,0,0.05)] ring-1 ring-stone-200 dark:ring-zinc-700">
                  {/* Dish header */}
                  <div className="mb-5 flex items-center gap-3">
                    <img
                      src="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=120&h=120&fit=crop&q=80"
                      alt="Chicken Biryani"
                      className="h-12 w-12 rounded-2xl object-cover ring-1 ring-stone-200 dark:ring-zinc-700"
                    />
                    <div>
                      <div className="text-sm font-semibold text-stone-900 dark:text-zinc-100">Chicken Biryani</div>
                      <div className="text-xs text-stone-400 dark:text-zinc-500">1 standard serving · 520 kcal</div>
                    </div>
                  </div>
                  {/* Macro bars */}
                  <div className="space-y-3">
                    <MacroBar label="Protein" value={32} max={50} unit="g" color="#059669" />
                    <MacroBar label="Carbs" value={58} max={80} unit="g" color="#059669" />
                    <MacroBar label="Fat" value={16} max={30} unit="g" color="#D97706" />
                  </div>
                  {/* Micro info */}
                  <div className="mt-5 flex items-center justify-between rounded-xl bg-stone-50 dark:bg-zinc-800 px-4 py-3">
                    <div className="text-center">
                      <div className="text-xs text-stone-400 dark:text-zinc-500">Fiber</div>
                      <div className="text-sm font-semibold text-stone-800 dark:text-zinc-200">3g</div>
                    </div>
                    <div className="h-6 w-px bg-stone-200" />
                    <div className="text-center">
                      <div className="text-xs text-stone-400 dark:text-zinc-500">Sodium</div>
                      <div className="text-sm font-semibold text-stone-800 dark:text-zinc-200">680mg</div>
                    </div>
                    <div className="h-6 w-px bg-stone-200" />
                    <div className="text-center">
                      <div className="text-xs text-stone-400 dark:text-zinc-500">Servings</div>
                      <div className="text-sm font-semibold text-stone-800 dark:text-zinc-200">1.0</div>
                    </div>
                  </div>
                </div>
                {/* Floating accuracy badge */}
                <div className="absolute -top-3 -right-3 rounded-2xl bg-white dark:bg-zinc-900 p-3 shadow-md ring-1 ring-stone-200 dark:ring-zinc-700">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/10">
                      <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                      </svg>
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-stone-800 dark:text-zinc-200">Macro Accurate</div>
                      <div className="text-[10px] text-stone-400 dark:text-zinc-500">Per serving</div>
                    </div>
                  </div>
                </div>
                {/* Floating dish count badge */}
                <div className="absolute -bottom-4 -left-4 rounded-2xl bg-white dark:bg-zinc-900 p-4 shadow-md ring-1 ring-stone-200 dark:ring-zinc-700">
                  <div className="text-2xl font-bold text-stone-900 dark:text-zinc-100 font-serif">215+</div>
                  <div className="text-xs text-stone-500 dark:text-zinc-500 mt-0.5">Seeded dishes</div>
                </div>
              </div>
              {/* Secondary floating food image */}
              <div className="absolute -bottom-8 -right-8 hidden lg:block">
                <img
                  src="https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=200&h=200&fit=crop&q=80"
                  alt="Butter Chicken"
                  className="h-28 w-28 rounded-2xl object-cover shadow-xl ring-2 ring-white dark:ring-zinc-800 animate-float"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Trust / Social Proof — DARK CONTRAST ─────────────────────── */}
      <section className="bg-zinc-900 dark:bg-zinc-950 py-16">
        <div className="mx-auto max-w-5xl px-6 text-center">
          <div className="mb-4 flex justify-center gap-1">
            {[...Array(5)].map((_, i) => (
              <svg key={i} className="h-5 w-5 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
          <h2 className="text-2xl font-semibold text-stone-900 dark:text-zinc-100 md:text-3xl font-serif">
            Built for the South Asian diaspora.
          </h2>
          <p className="mt-3 text-stone-400 dark:text-zinc-500">
            The smartest way to track cultural cuisines — from Karachi to Colombo.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <button className="inline-flex items-center gap-3 rounded-2xl border border-stone-200 dark:border-zinc-700 bg-stone-50 dark:bg-zinc-800 px-6 py-3 text-left transition-all duration-200 hover:bg-stone-100 dark:bg-zinc-800 hover:border-stone-300 active:scale-[0.97]">
              <svg className="h-7 w-7 text-stone-900 dark:text-zinc-100" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
              </svg>
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wide text-stone-500 dark:text-zinc-500">Download on the</div>
                <div className="text-sm font-semibold text-stone-900 dark:text-zinc-100">App Store</div>
              </div>
            </button>
            <button className="inline-flex items-center gap-3 rounded-2xl border border-stone-200 dark:border-zinc-700 bg-stone-50 dark:bg-zinc-800 px-6 py-3 text-left transition-all duration-200 hover:bg-stone-100 dark:bg-zinc-800 hover:border-stone-300 active:scale-[0.97]">
              <svg className="h-7 w-7 text-stone-900 dark:text-zinc-100" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3.609 1.814 13.792 12 3.61 22.186a.996.996 0 0 1-.61-.92V2.734a1 1 0 0 1 .609-.92zm10.89 10.893 2.302 2.302-10.937 6.333 8.635-8.635zm3.199-1.707 2.173 1.262a1.001 1.001 0 0 1 0 1.74l-2.173 1.262-2.535-2.535 2.535-2.729zM5.864 2.658 16.8 8.99l-2.302 2.302-8.634-8.634z" />
              </svg>
              <div>
                <div className="text-[10px] font-medium uppercase tracking-wide text-stone-500 dark:text-zinc-500">Get it on</div>
                <div className="text-sm font-semibold text-stone-900 dark:text-zinc-100">Google Play</div>
              </div>
            </button>
          </div>
        </div>
      </section>

      {/* ── Features — 3-Column Bento Grid ──────────────────────────── */}
      <section id="features" className="py-24 md:py-32 bg-background">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-16 md:mb-20 text-center">
            <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-emerald-600">Features</p>
            <h2 className="text-3xl font-semibold tracking-tight text-stone-900 dark:text-zinc-100 md:text-4xl font-serif">
              Nutrition tracking made effortless for our food.
            </h2>
            <p className="mt-4 text-lg text-stone-500 dark:text-zinc-500 max-w-xl mx-auto">
              Built specifically for South Asian cuisine — not a generic Western diet app.
            </p>
          </div>

          {/* Bento Grid */}
          <div className="grid gap-5 md:grid-cols-3">
            {/* Card 1 — Food Library (Tall) */}
            <div id="how-it-works" className="md:row-span-2 rounded-3xl bg-white dark:bg-zinc-900 p-8 ring-1 ring-stone-200 dark:ring-zinc-700/60 shadow-sm transition-all duration-300 hover:shadow-md md:p-10">
              <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-xl">
                🍛
              </div>
              <h3 className="text-xl font-semibold text-stone-900 dark:text-zinc-100 font-serif">
                215+ South Asian dishes
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-stone-500 dark:text-zinc-500">
                From Chicken Biryani to Gulab Jamun — every dish pre-loaded
                with accurate macros per serving. Search, log, track.
              </p>
              {/* Mock food list */}
              <div className="mt-6 space-y-2.5">
                {[
                  { name: "Chicken Biryani", cal: 520, p: 32, img: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=80&h=80&fit=crop&q=60" },
                  { name: "Butter Chicken", cal: 450, p: 30, img: "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=80&h=80&fit=crop&q=60" },
                  { name: "Daal Chawal", cal: 420, p: 20, img: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=80&h=80&fit=crop&q=60" },
                  { name: "Paneer Tikka", cal: 420, p: 22, img: "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=80&h=80&fit=crop&q=60" },
                  { name: "Garlic Naan", cal: 260, p: 7, img: "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=80&h=80&fit=crop&q=60" },
                ].map((d) => (
                  <div key={d.name} className="flex items-center gap-3 rounded-xl bg-stone-50 dark:bg-zinc-800 px-3.5 py-2.5">
                    <img
                      src={d.img}
                      alt={d.name}
                      className="h-9 w-9 rounded-lg object-cover ring-1 ring-stone-200 dark:ring-zinc-700"
                    />
                    <span className="flex-1 text-xs font-medium text-stone-700 dark:text-zinc-300">{d.name}</span>
                    <div className="flex gap-2">
                      <span className="text-[10px] font-medium text-emerald-600">{d.cal} cal</span>
                      <span className="text-[10px] font-medium text-emerald-600">{d.p}g P</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Card 2 — AI Streaming (Wide) */}
            <div className="md:col-span-2 rounded-3xl bg-white dark:bg-zinc-900 p-8 ring-1 ring-stone-200 dark:ring-zinc-700/60 shadow-sm transition-all duration-300 hover:shadow-md md:p-10">
              <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:gap-12">
                <div className="flex-1">
                  <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-xl">
                    <img
                      src="https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=100&h=100&fit=crop&q=60"
                      alt="AI Meal Plans"
                      className="h-10 w-10 rounded-xl object-cover"
                    />
                  </div>
                  <h3 className="text-xl font-semibold text-stone-900 dark:text-zinc-100 font-serif">
                    Dual-pipeline AI streaming
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-stone-500 dark:text-zinc-500">
                    Get personalized meal plans AND workout routines generated in real-time.
                    Watch the AI build your plan line by line — copy, save, or regenerate instantly.
                  </p>
                  <Link
                    href="/onboarding"
                    className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-emerald-600 hover:text-emerald-600 transition-colors"
                  >
                    Try the AI generator
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                    </svg>
                  </Link>
                </div>
                {/* Streaming mock */}
                <div className="flex-shrink-0 rounded-2xl bg-stone-900 p-5 font-mono text-xs leading-relaxed text-stone-300 dark:text-zinc-600 lg:w-72">
                  <div className="mb-2 text-[10px] font-medium text-emerald-600 uppercase tracking-wider">Streaming</div>
                  <div className="space-y-1.5">
                    <div><span className="text-stone-600 dark:text-zinc-400">##</span> High-Protein Plan</div>
                    <div><span className="text-stone-600 dark:text-zinc-400">###</span> Breakfast</div>
                    <div>- Omelette + Roti</div>
                    <div>- Greek yogurt bowl</div>
                    <div><span className="text-stone-600 dark:text-zinc-400">###</span> Lunch</div>
                    <div>- Chicken Karahi</div>
                    <div>- Brown rice (1 cup)</div>
                    <div className="mt-2 inline-block h-4 w-0.5 animate-pulse bg-emerald-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Card 3 — TDEE Engine (Wide) */}
            <div className="md:col-span-2 rounded-3xl bg-white dark:bg-zinc-900 p-8 ring-1 ring-stone-200 dark:ring-zinc-700/60 shadow-sm transition-all duration-300 hover:shadow-md md:p-10">
              <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:gap-12">
                {/* Macro targets mock */}
                <div className="flex-shrink-0 rounded-2xl bg-stone-50 dark:bg-zinc-800 p-5 ring-1 ring-stone-200 dark:ring-zinc-700/50 lg:w-64">
                  <div className="mb-3 text-[10px] font-medium text-stone-400 dark:text-zinc-500 uppercase tracking-wider">Your Daily Targets</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl bg-white dark:bg-zinc-900 p-3 ring-1 ring-stone-200 dark:ring-zinc-700/50">
                      <div className="text-[10px] text-stone-400 dark:text-zinc-500">Calories</div>
                      <div className="text-lg font-bold text-stone-900 dark:text-zinc-100 font-serif">2,350</div>
                    </div>
                    <div className="rounded-xl bg-white dark:bg-zinc-900 p-3 ring-1 ring-stone-200 dark:ring-zinc-700/50">
                      <div className="text-[10px] text-stone-400 dark:text-zinc-500">Protein</div>
                      <div className="text-lg font-bold text-emerald-600 font-serif">165g</div>
                    </div>
                    <div className="rounded-xl bg-white dark:bg-zinc-900 p-3 ring-1 ring-stone-200 dark:ring-zinc-700/50">
                      <div className="text-[10px] text-stone-400 dark:text-zinc-500">Carbs</div>
                      <div className="text-lg font-bold text-emerald-600 font-serif">280g</div>
                    </div>
                    <div className="rounded-xl bg-white dark:bg-zinc-900 p-3 ring-1 ring-stone-200 dark:ring-zinc-700/50">
                      <div className="text-[10px] text-stone-400 dark:text-zinc-500">Fat</div>
                      <div className="text-lg font-bold text-amber-600 font-serif">78g</div>
                    </div>
                  </div>
                </div>
                <div className="flex-1">
                  <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-xl">
                    <img
                      src="https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=100&h=100&fit=crop&q=60"
                      alt="Macro Targets"
                      className="h-10 w-10 rounded-xl object-cover"
                    />
                  </div>
                  <h3 className="text-xl font-semibold text-stone-900 dark:text-zinc-100 font-serif">
                    Mifflin-St Jeor TDEE engine
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-stone-500 dark:text-zinc-500">
                    Your calorie and macro targets are calculated using the gold-standard
                    Mifflin-St Jeor equation — personalized to your body, activity level,
                    and goals. Updated live whenever your stats change.
                  </p>
                  <Link
                    href="/onboarding"
                    className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-emerald-600 hover:text-emerald-600 transition-colors"
                  >
                    Calculate your TDEE
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
      <section id="pricing" className="bg-stone-100 dark:bg-zinc-800/50 py-24 md:py-32">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-14 text-center">
            <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-emerald-600">Pricing</p>
            <h2 className="text-3xl font-semibold tracking-tight text-stone-900 dark:text-zinc-100 md:text-4xl font-serif">
              Simple, transparent pricing.
            </h2>
            <p className="mt-3 text-stone-500 dark:text-zinc-500">Start free. Upgrade when you&apos;re ready.</p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 max-w-2xl mx-auto">
            {/* Free tier */}
            <div className="rounded-3xl border border-stone-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-8 shadow-sm transition-all duration-300 hover:shadow-md">
              <p className="text-sm font-medium text-stone-400 dark:text-zinc-500">Free</p>
              <p className="mt-2 text-4xl font-bold text-stone-900 dark:text-zinc-100 font-serif">$0</p>
              <p className="mt-1 text-sm text-stone-400 dark:text-zinc-500">forever</p>
              <ul className="mt-6 space-y-3.5 text-sm text-stone-600 dark:text-zinc-400">
                <li className="flex items-center gap-3">
                  <span className="text-stone-300 dark:text-zinc-600">—</span> 3 meal plans / month
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-stone-300 dark:text-zinc-600">—</span> Food library (215+ dishes)
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-stone-300 dark:text-zinc-600">—</span> Progress tracking
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-full border border-stone-200 dark:border-zinc-700 py-3 text-center text-sm font-medium text-stone-700 dark:text-zinc-300 transition-all duration-200 hover:bg-stone-50 dark:bg-zinc-800 hover:border-stone-300 active:scale-[0.97]"
              >
                Get started
              </Link>
            </div>
            {/* Pro tier */}
            <div className="relative rounded-3xl border-2 border-emerald-600 bg-white dark:bg-zinc-900 p-8 shadow-lg shadow-emerald-600/5 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-600/10">
              <div className="absolute -top-3.5 right-6 rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-stone-900 dark:text-zinc-100 shadow-md shadow-emerald-600/20">
                Most Popular
              </div>
              <p className="text-sm font-medium text-stone-400 dark:text-zinc-500">Pro</p>
              <p className="mt-2 text-4xl font-bold text-stone-900 dark:text-zinc-100 font-serif">$9</p>
              <p className="mt-1 text-sm text-stone-400 dark:text-zinc-500">/month</p>
              <ul className="mt-6 space-y-3.5 text-sm text-stone-600 dark:text-zinc-400">
                <li className="flex items-center gap-3">
                  <span className="text-emerald-600 font-bold">✓</span> Unlimited meal plans
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-emerald-600 font-bold">✓</span> AI workout generator
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-emerald-600 font-bold">✓</span> Saved plans archive
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-emerald-600 font-bold">✓</span> Priority support
                </li>
              </ul>
              <Link
                href="/onboarding"
                className="mt-8 block w-full rounded-full bg-emerald-600 py-3 text-center text-sm font-semibold text-stone-900 dark:text-zinc-100 shadow-md shadow-emerald-600/20 transition-all duration-200 hover:bg-emerald-700 hover:shadow-lg active:scale-[0.97]"
              >
                Start free trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA — DARK CONTRAST ─────────────────────────────── */}
      <section className="bg-zinc-900 dark:bg-zinc-950 py-24">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-semibold text-stone-900 dark:text-zinc-100 md:text-4xl font-serif">
            Your goals. Your food. Your plan.
          </h2>
          <p className="mt-4 text-stone-400 dark:text-zinc-500 text-lg">
            Start building sustainable fitness habits with the food you love.
          </p>
          <Link
            href="/onboarding"
            className="mt-8 inline-flex items-center gap-2.5 rounded-full bg-emerald-600 px-8 py-3.5 text-sm font-semibold text-stone-900 dark:text-zinc-100 shadow-lg shadow-emerald-600/20 transition-all duration-200 hover:shadow-xl hover:shadow-emerald-600/30 hover:bg-emerald-700 active:scale-[0.97]"
          >
            Start for free
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="bg-zinc-900 dark:bg-zinc-950 border-t border-stone-200 dark:border-zinc-700 py-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 text-sm text-stone-500 dark:text-zinc-500 md:flex-row md:items-center md:justify-between">
          <p>© 2026 South Asian Fitness.</p>
          <div className="flex gap-6">
            <Link href="/auth/login" className="hover:text-stone-900 dark:text-zinc-100 transition-colors">Login</Link>
            <Link href="/privacy" className="hover:text-stone-900 dark:text-zinc-100 transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-stone-900 dark:text-zinc-100 transition-colors">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ── MacroBar — clean linear progress ───────────────────────────────── */
function MacroBar({
  label,
  value,
  max,
  unit,
  color,
}: {
  label: string;
  value: number;
  max: number;
  unit: string;
  color: string;
}) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium text-stone-500 dark:text-zinc-500">{label}</span>
        <span className="text-xs font-semibold text-stone-700 dark:text-zinc-300 tabular-nums">
          {value}
          {unit}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-stone-100 dark:bg-zinc-800">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
