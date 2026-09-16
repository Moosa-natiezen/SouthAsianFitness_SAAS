import Image from "next/image";
import Link from "next/link";

/* ── Landing Page — Sleek Health Data (forced dark) ─────────────────
   Single dark theme: bg-zinc-950 + glassmorphism (bg-white/5 +
   backdrop-blur + border-white/10) with warm honey/amber gradient
   accents for primary CTAs and highlights. No light-mode variants —
   the root is always dark regardless of the app theme toggle.       */

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-clip bg-zinc-950 text-zinc-100 antialiased">
      {/* Ambient glow backdrop */}
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute -top-32 left-1/2 h-105 w-[52rem] -translate-x-1/2 rounded-full bg-amber-500/10 blur-3xl" />
        <div className="absolute top-1/3 -right-40 h-96 w-96 rounded-full bg-amber-500/8 blur-3xl" />
        <div className="absolute bottom-0 -left-40 h-96 w-96 rounded-full bg-orange-600/6 blur-3xl" />
      </div>

      <SiteNav />
      <Hero />
      <FeatureGrid />
      <PricingTeaser />
      <FinalCta />
      <SiteFooter />
    </div>
  );
}

/* ── Nav ──────────────────────────────────────────────────────────────── */

function SiteNav() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-zinc-950/70 backdrop-blur-xl print:hidden">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 text-xs font-bold text-zinc-950 shadow-sm shadow-amber-500/30">
            SA
          </div>
          <span className="text-sm font-semibold tracking-tight text-zinc-100">
            South Asian Fitness
          </span>
        </div>
        <nav className="hidden items-center gap-8 text-sm text-zinc-400 md:flex">
          <a href="#features" className="transition-colors hover:text-zinc-100">
            Features
          </a>
          <a
            href="#how-it-works"
            className="transition-colors hover:text-zinc-100"
          >
            How it works
          </a>
          <a href="#pricing" className="transition-colors hover:text-zinc-100">
            Pricing
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <Link
            href="/auth/login"
            className="text-sm text-zinc-400 transition-colors hover:text-zinc-100"
          >
            Log in
          </Link>
          <Link
            href="/auth/signup"
            className="rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-5 py-2 text-sm font-semibold text-zinc-950 shadow-md shadow-amber-500/25 transition-all duration-200 hover:shadow-lg hover:shadow-amber-500/40 active:scale-[0.97]"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}

/* ── Hero ─────────────────────────────────────────────────────────────── */

function Hero() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid items-center gap-14 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
          {/* Left — copy & CTA */}
          <div className="text-center lg:text-left">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 backdrop-blur-md">
              <div className="h-1.5 w-1.5 rounded-full bg-amber-400" />
              <span className="text-xs font-medium tracking-wide text-amber-300">
                AI-Powered Nutrition
              </span>
            </div>
            <h1 className="font-serif text-4xl font-semibold leading-[1.08] tracking-tight text-zinc-50 md:text-5xl lg:text-[3.5rem]">
              Track authentic{" "}
              <span className="bg-gradient-to-r from-amber-300 to-orange-400 bg-clip-text text-transparent">
                Desi macros
              </span>{" "}
              in seconds
            </h1>
            <p className="mx-auto mt-6 max-w-lg text-lg leading-relaxed text-zinc-400 lg:mx-0">
              AI meal plans built for the food you actually eat — Biryani,
              Daal, Karahi, Roti — with precise macros and calorie targets
              tuned to your body.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
              <Link
                href="/onboarding"
                className="inline-flex items-center gap-2.5 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-8 py-3.5 text-sm font-semibold text-zinc-950 shadow-lg shadow-amber-500/30 transition-all duration-200 hover:shadow-xl hover:shadow-amber-500/40 active:scale-[0.97]"
              >
                Get Started
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"
                  />
                </svg>
              </Link>
              <a
                href="#how-it-works"
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-8 py-3.5 text-sm font-medium text-zinc-300 backdrop-blur-md transition-all duration-200 hover:border-white/20 hover:bg-white/10 active:scale-[0.97]"
              >
                See how it works
              </a>
            </div>
            <p className="mt-6 text-xs text-zinc-500">
              Free to start — 3 AI meal plans every month, no card required.
            </p>
          </div>

          {/* Right — floating macro-tracking card */}
          <div className="relative flex justify-center lg:justify-end">
            <div className="absolute inset-0 m-auto h-[60%] w-[60%] rounded-full bg-amber-500/8 blur-3xl" />
            <div className="relative w-full max-w-md">
              <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur-md">
                {/* Dish header */}
                <div className="mb-5 flex items-center gap-3">
                  <Image
                    src="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=120&h=120&fit=crop&q=80"
                    alt="Chicken Biryani served in a traditional bowl with saffron rice"
                    width={48}
                    height={48}
                    sizes="48px"
                    className="h-12 w-12 rounded-2xl object-cover ring-1 ring-white/15"
                    priority
                  />
                  <div>
                    <div className="text-sm font-semibold text-zinc-100">
                      Chicken Biryani
                    </div>
                    <div className="text-xs text-zinc-500">
                      1 standard serving · 520 kcal
                    </div>
                  </div>
                </div>
                {/* Macro bars */}
                <div className="space-y-3">
                  <MacroBar label="Protein" value={32} max={50} unit="g" barClass="bg-emerald-400" textClass="text-emerald-300" />
                  <MacroBar label="Carbs" value={58} max={80} unit="g" barClass="bg-amber-400" textClass="text-amber-300" />
                  <MacroBar label="Fat" value={16} max={30} unit="g" barClass="bg-orange-500" textClass="text-orange-300" />
                </div>
                {/* Micro info strip */}
                <div className="mt-5 flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-4 py-3">
                  <StatMini label="Fiber" value="3g" />
                  <div className="h-6 w-px bg-white/10" />
                  <StatMini label="Sodium" value="680mg" />
                  <div className="h-6 w-px bg-white/10" />
                  <StatMini label="Servings" value="1.0" />
                </div>
              </div>

              {/* Floating accuracy badge */}
              <div className="absolute -top-3 -right-3 hidden rounded-2xl border border-white/10 bg-zinc-900/90 p-3 shadow-lg backdrop-blur-md sm:block">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/10">
                    <svg
                      className="h-4 w-4 text-emerald-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                      />
                    </svg>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-zinc-200">
                      Macro Accurate
                    </div>
                    <div className="text-[10px] text-zinc-500">Per serving</div>
                  </div>
                </div>
              </div>

              {/* Floating dish count badge */}
              <div className="absolute -bottom-4 -left-4 hidden rounded-2xl border border-white/10 bg-zinc-900/90 p-4 shadow-lg backdrop-blur-md sm:block">
                <div className="font-serif text-2xl font-bold text-zinc-50">
                  215+
                </div>
                <div className="mt-0.5 text-xs text-zinc-500">
                  Seeded dishes
                </div>
              </div>

              {/* Floating food image */}
              <div className="absolute -bottom-8 -right-8 hidden lg:block">
                <Image
                  src="https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=200&h=200&fit=crop&q=80"
                  alt="Rich butter chicken curry — one of 215+ South Asian dishes tracked in the food library"
                  width={112}
                  height={112}
                  sizes="112px"
                  className="animate-float h-28 w-28 rounded-2xl object-cover shadow-xl ring-2 ring-white/15"
                  priority
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function StatMini({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-sm font-semibold text-zinc-200">{value}</div>
    </div>
  );
}

/* ── Feature grid ─────────────────────────────────────────────────────── */

function FeatureGrid() {
  return (
    <section id="features" className="py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-16 text-center md:mb-20">
          <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-amber-400">
            Features
          </p>
          <h2 className="font-serif text-3xl font-semibold tracking-tight text-zinc-50 md:text-4xl">
            Everything you need to eat right.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-zinc-400">
            Built specifically for South Asian cuisine — not a generic Western
            diet app.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {/* Card 1 — AI meal generation */}
          <div
            id="how-it-works"
            className="card-hover rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-md"
          >
            <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-400/10 text-xl">
              🍛
            </div>
            <h3 className="font-serif text-xl font-semibold text-zinc-100">
              AI Meal Generation
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">
              Personalized Desi meal plans streamed line by line — macro-balanced
              around your targets, from Chicken Karahi to Chana Chaat.
            </p>
            {/* Streaming mock */}
            <div className="mt-6 rounded-2xl border border-white/5 bg-zinc-900/80 p-5 font-mono text-xs leading-relaxed text-zinc-300">
              <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-amber-400">
                Streaming
              </div>
              <div className="space-y-1.5">
                <div>
                  <span className="text-zinc-600">##</span> High-Protein Plan
                </div>
                <div>
                  <span className="text-zinc-600">###</span> Lunch
                </div>
                <div>- Chicken Karahi + 2 Roti</div>
                <div>- Cucumber Raita</div>
                <div className="mt-2 inline-block h-4 w-0.5 animate-pulse bg-amber-400" />
              </div>
            </div>
          </div>

          {/* Card 2 — WhatsApp logging */}
          <div className="card-hover rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-md">
            <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-400/10 text-xl">
              💬
            </div>
            <h3 className="font-serif text-xl font-semibold text-zinc-100">
              WhatsApp Logging
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">
              Text what you ate in plain words. The AI extracts every dish,
              estimates the macros, and replies with your running daily total.
            </p>
            {/* Chat mock */}
            <div className="mt-6 space-y-2.5">
              <div className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-sm bg-amber-400/15 px-3.5 py-2.5 text-xs text-amber-100">
                🥘 2 aloo parathas + chai
              </div>
              <div className="w-fit max-w-[90%] rounded-2xl rounded-bl-sm border border-white/10 bg-white/5 px-3.5 py-2.5 text-xs text-zinc-300">
                <div className="font-semibold text-zinc-100">
                  ✅ Logged · 610 kcal
                </div>
                <div className="mt-0.5 text-zinc-400">P 14g · C 78g · F 24g</div>
                <div className="mt-1.5 text-emerald-300">
                  🎯 1,290 kcal left today
                </div>
              </div>
            </div>
          </div>

          {/* Card 3 — custom calorie targets */}
          <div className="card-hover rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-md">
            <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-500/10 text-xl">
              🎯
            </div>
            <h3 className="font-serif text-xl font-semibold text-zinc-100">
              Custom Calorie Targets
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">
              Mifflin-St Jeor TDEE math as your starting point — then override
              any target by hand. Every plan adapts to the numbers you set.
            </p>
            {/* Targets mock */}
            <div className="mt-6 grid grid-cols-2 gap-3">
              <TargetChip label="Calories" value="2,350" accent="text-zinc-50" />
              <TargetChip label="Protein" value="165g" accent="text-emerald-300" />
              <TargetChip label="Carbs" value="280g" accent="text-amber-300" />
              <TargetChip label="Fat" value="78g" accent="text-orange-300" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TargetChip({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-zinc-900/80 p-3">
      <div className="text-[10px] text-zinc-500">{label}</div>
      <div className={`font-serif text-lg font-bold ${accent}`}>{value}</div>
    </div>
  );
}

/* ── Pricing teaser ───────────────────────────────────────────────────── */

function PricingTeaser() {
  return (
    <section id="pricing" className="py-24 md:py-32">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-14 text-center">
          <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-amber-400">
            Pricing
          </p>
          <h2 className="font-serif text-3xl font-semibold tracking-tight text-zinc-50 md:text-4xl">
            Simple, transparent pricing.
          </h2>
          <p className="mt-3 text-zinc-400">
            Start free. Upgrade when you&apos;re ready.
          </p>
        </div>

        <div className="mx-auto grid max-w-2xl gap-8 md:grid-cols-2">
          {/* Free tier — quiet */}
          <div className="card-hover rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-md">
            <p className="text-sm font-medium text-zinc-500">Free</p>
            <p className="font-serif mt-2 text-4xl font-bold text-zinc-50">$0</p>
            <p className="mt-1 text-sm text-zinc-500">forever</p>
            <ul className="mt-6 space-y-3.5 text-sm text-zinc-400">
              <li className="flex items-center gap-3">
                <span className="text-zinc-600">—</span> 3 meal plans / month
              </li>
              <li className="flex items-center gap-3">
                <span className="text-zinc-600">—</span> Food library (215+
                dishes)
              </li>
              <li className="flex items-center gap-3">
                <span className="text-zinc-600">—</span> Progress tracking
              </li>
            </ul>
            <Link
              href="/onboarding"
              className="mt-8 block w-full rounded-full border border-white/10 bg-white/5 py-3 text-center text-sm font-medium text-zinc-200 transition-all duration-200 hover:border-white/20 hover:bg-white/10 active:scale-[0.97]"
            >
              Get started
            </Link>
          </div>

          {/* Pro tier — high contrast */}
          <div className="card-hover relative rounded-3xl border-2 border-amber-400/50 bg-gradient-to-b from-amber-400/10 to-white/5 p-8 shadow-[0_0_60px_rgba(251,191,36,0.12)] backdrop-blur-md">
            <div className="absolute -top-3.5 right-6 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-3 py-1 text-xs font-semibold text-zinc-950 shadow-md shadow-amber-500/30">
              Most Popular
            </div>
            <p className="text-sm font-medium text-amber-300/80">Pro Member</p>
            <p className="font-serif mt-2 text-4xl font-bold text-zinc-50">$9</p>
            <p className="mt-1 text-sm text-zinc-500">/month</p>
            <ul className="mt-6 space-y-3.5 text-sm text-zinc-300">
              <li className="flex items-center gap-3">
                <span className="font-bold text-amber-400">✓</span> Unlimited
                meal plans
              </li>
              <li className="flex items-center gap-3">
                <span className="font-bold text-amber-400">✓</span> AI workout
                generator
              </li>
              <li className="flex items-center gap-3">
                <span className="font-bold text-amber-400">✓</span> WhatsApp +
                voice logging
              </li>
              <li className="flex items-center gap-3">
                <span className="font-bold text-amber-400">✓</span> Saved plans
                archive
              </li>
            </ul>
            <Link
              href="/onboarding"
              className="mt-8 block w-full rounded-full bg-gradient-to-r from-amber-400 to-orange-500 py-3 text-center text-sm font-semibold text-zinc-950 shadow-md shadow-amber-500/30 transition-all duration-200 hover:shadow-lg hover:shadow-amber-500/40 active:scale-[0.97]"
            >
              Start free trial
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Final CTA ────────────────────────────────────────────────────────── */

function FinalCta() {
  return (
    <section className="relative py-28 md:py-32">
      <div className="mx-auto max-w-3xl px-6 text-center">
        <div className="card-hover rounded-[2.5rem] border border-white/10 bg-white/5 px-8 py-16 backdrop-blur-md">
          <h2 className="font-serif text-3xl font-semibold text-zinc-50 md:text-4xl">
            Your goals. Your food. Your plan.
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            Start building sustainable fitness habits with the food you love.
          </p>
          <Link
            href="/onboarding"
            className="mt-8 inline-flex items-center gap-2.5 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-8 py-3.5 text-sm font-semibold text-zinc-950 shadow-lg shadow-amber-500/30 transition-all duration-200 hover:shadow-xl hover:shadow-amber-500/40 active:scale-[0.97]"
          >
            Get Started
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"
              />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}

/* ── Footer ───────────────────────────────────────────────────────────── */

function SiteFooter() {
  return (
    <footer className="border-t border-white/10 py-8 print:hidden">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 text-sm text-zinc-500 md:flex-row md:items-center md:justify-between">
        <p>&copy; 2026 South Asian Fitness.</p>
        <div className="flex gap-6">
          <Link href="/auth/login" className="transition-colors hover:text-zinc-100">
            Login
          </Link>
          <Link href="/privacy" className="transition-colors hover:text-zinc-100">
            Privacy
          </Link>
          <Link href="/terms" className="transition-colors hover:text-zinc-100">
            Terms
          </Link>
        </div>
      </div>
    </footer>
  );
}

/* ── MacroBar — clean linear progress ─────────────────────────────────── */

function MacroBar({
  label,
  value,
  max,
  unit,
  barClass,
  textClass,
}: {
  label: string;
  value: number;
  max: number;
  unit: string;
  barClass: string;
  textClass: string;
}) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-400">{label}</span>
        <span className={`text-xs font-semibold tabular-nums ${textClass}`}>
          {value}
          {unit}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${barClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
