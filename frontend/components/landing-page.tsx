"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { AnimateIn, StaggerIn } from "@/components/animate-in";
import { FeatureScroll } from "@/components/landing/feature-scroll";
import { PricingSection } from "@/components/landing/pricing-section";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

/* ── Data ──────────────────────────────────────────────────────────────── */

const oldWay = [
  { icon: "🚫", title: "Bland chicken & rice", desc: "Same meals every day. No flavour, no culture." },
  { icon: "📉", title: "Restrictive diets", desc: "Cut out entire food groups you grew up with." },
  { icon: "🤷", title: "Guesswork macros", desc: "No idea if you're hitting protein or overeating carbs." },
  { icon: "💸", title: "Expensive meal plans", desc: "Imported supplements and organic-only shopping lists." },
];

const flexAiWay = [
  { icon: "🍛", title: "Your cultural cuisine", desc: "Dal, biryani, tikka, paratha — optimized, not eliminated." },
  { icon: "🎯", title: "Precision macros", desc: "Every meal calculated to hit your exact targets." },
  { icon: "🤖", title: "AI-powered plans", desc: "Generate personalized plans in seconds, not hours." },
  { icon: "💰", title: "Budget-aware", desc: "Plans that fit your grocery budget and local prices." },
];

/* ── Main Landing Page ──────────────────────────────────────────────── */

export function LandingPage() {
  const bentoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = bentoRef.current;
    if (!el) return;

    const ctx = gsap.context(() => {
      const cards = el.querySelectorAll("[data-bento]");
      gsap.fromTo(
        cards,
        { opacity: 0, y: 60, filter: "blur(8px)" },
        {
          opacity: 1,
          y: 0,
          filter: "blur(0px)",
          duration: 1,
          stagger: 0.12,
          ease: "power3.out",
          scrollTrigger: {
            trigger: el,
            start: "top 75%",
            end: "bottom 25%",
            toggleActions: "play none none reverse",
          },
        },
      );
    }, el);

    return () => ctx.revert();
  }, []);

  return (
    <div className="dark min-h-screen bg-[#0A0A0A] text-[#FAFAFA] overflow-x-hidden">
      {/* ── Navigation ─────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/6 bg-[#0A0A0A]/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 text-sm font-bold text-[#0A0A0A]">
              SA
            </div>
            <p className="text-lg font-semibold text-[#FAFAFA]">South Asian Fitness</p>
          </div>
          <nav className="hidden items-center gap-8 text-sm font-medium text-[#A1A1AA] md:flex">
            <a href="#features" className="transition hover:text-[#FAFAFA]">Features</a>
            <a href="#how-it-works" className="transition hover:text-[#FAFAFA]">How it works</a>
            <a href="#pricing" className="transition hover:text-[#FAFAFA]">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href="/auth/login"
              className="rounded-xl px-4 py-2 text-sm font-medium text-[#A1A1AA] transition hover:text-[#FAFAFA]"
            >
              Log in
            </Link>
            <Link
              href="/auth/signup"
              className="rounded-xl bg-amber-500 px-5 py-2.5 text-sm font-semibold text-[#0A0A0A] transition hover:bg-amber-400"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero Section — Minimalist ──────────────────────────────────── */}
      <section className="relative flex min-h-screen items-center overflow-hidden">
        {/* Subtle radial gradient — no orbs */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(245,158,11,0.06)_0%,_transparent_70%)]" />

        {/* Content */}
        <div className="relative z-10 mx-auto max-w-6xl px-6 pt-32 pb-20 md:pt-40">
          <div className="max-w-3xl">
            <AnimateIn delay={0.2} y={20} blur={4}>
              <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-1.5 text-sm font-medium text-amber-400 mb-8">
                <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
                AI-powered nutrition for South Asian cuisine
              </div>
            </AnimateIn>

            <AnimateIn delay={0.4} y={30} blur={6}>
              <h1 className="font-serif text-5xl font-bold leading-[1.1] tracking-tight md:text-7xl lg:text-8xl">
                Fitness that fits{" "}
                <span className="text-gradient-accent">your culture.</span>
                <br />
                <span className="text-[#A1A1AA]">Powered by AI.</span>
              </h1>
            </AnimateIn>

            <AnimateIn delay={0.6} y={25} blur={4}>
              <p className="mt-8 max-w-xl text-lg leading-relaxed text-[#A1A1AA] md:text-xl">
                Generate personalized, macro-optimized South Asian meal plans in seconds.
                Stop sacrificing the food you love to hit your goals.
              </p>
            </AnimateIn>

            <AnimateIn delay={0.8} y={20} blur={3}>
              <div className="mt-10 flex flex-col gap-4 sm:flex-row">
                <Link
                  href="/onboarding"
                  className="rounded-2xl bg-amber-500 px-8 py-4 text-center text-base font-bold text-[#0A0A0A] transition hover:bg-amber-400"
                >
                  Start Your Journey
                </Link>
                <a
                  href="#how-it-works"
                  className="flex items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] px-8 py-4 text-base font-medium text-[#A1A1AA] transition-all hover:bg-white/[0.06] hover:text-[#FAFAFA]"
                >
                  See how it works →
                </a>
              </div>
            </AnimateIn>

            <AnimateIn delay={1.0} y={15} blur={2}>
              <div className="mt-12 flex flex-wrap gap-6 text-sm text-[#71717A]">
                <span className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-amber-500" />
                  215+ South Asian foods
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-amber-500" />
                  Multi-country support
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-amber-500" />
                  Budget-aware plans
                </span>
              </div>
            </AnimateIn>
          </div>
        </div>
      </section>

      {/* ── Bento Grid: Old Way vs FlexAI ──────────────────────────────── */}
      <section id="features" className="relative py-24 md:py-32">
        <div className="mx-auto max-w-6xl px-6">
          <AnimateIn>
            <div className="mb-16 text-center">
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-amber-500">
                The problem
              </p>
              <h2 className="mt-4 font-serif text-3xl font-bold text-[#FAFAFA] md:text-5xl">
                The old way doesn&apos;t work.
              </h2>
            </div>
          </AnimateIn>

          <div ref={bentoRef} className="grid gap-6 md:grid-cols-2">
            {/* Old Way */}
            <div className="space-y-4">
              <div className="mb-6 flex items-center gap-3">
                <span className="rounded-lg bg-red-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-red-400">
                  The old way
                </span>
                <div className="h-px flex-1 bg-red-500/10" />
              </div>
              <StaggerIn stagger={0.1}>
                {oldWay.map((item) => (
                  <div
                    key={item.title}
                    data-bento
                    className="rounded-2xl border border-white/6 bg-[#111111] p-5"
                  >
                    <div className="flex items-start gap-4">
                      <span className="text-2xl">{item.icon}</span>
                      <div>
                        <h3 className="font-medium text-[#A1A1AA]">{item.title}</h3>
                        <p className="mt-1 text-sm text-[#71717A]">{item.desc}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </StaggerIn>
            </div>

            {/* FlexAI Way */}
            <div className="space-y-4">
              <div className="mb-6 flex items-center gap-3">
                <span className="rounded-lg bg-amber-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-amber-500">
                  The FlexAI way
                </span>
                <div className="h-px flex-1 bg-amber-500/10" />
              </div>
              <StaggerIn stagger={0.1} delay={0.2}>
                {flexAiWay.map((item) => (
                  <div
                    key={item.title}
                    data-bento
                    className="rounded-2xl border border-white/6 bg-[#111111] p-5 transition-all duration-300 hover:border-amber-500/15 hover:bg-[#161616]"
                  >
                    <div className="flex items-start gap-4">
                      <span className="text-2xl">{item.icon}</span>
                      <div>
                        <h3 className="font-medium text-[#FAFAFA]">{item.title}</h3>
                        <p className="mt-1 text-sm text-[#71717A]">{item.desc}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </StaggerIn>
            </div>
          </div>
        </div>
      </section>

      {/* ── Feature Scroll: AI Streaming Demo ───────────────────────────── */}
      <div id="how-it-works">
        <FeatureScroll />
      </div>

      {/* ── Pricing ─────────────────────────────────────────────────────── */}
      <div id="pricing">
        <PricingSection />
      </div>

      {/* ── Final CTA ───────────────────────────────────────────────────── */}
      <section className="relative py-24 md:py-32">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-1/2 h-[400px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/[0.04] blur-[120px]" />
        </div>
        <div className="relative mx-auto max-w-3xl px-6 text-center">
          <AnimateIn>
            <h2 className="font-serif text-3xl font-bold text-[#FAFAFA] md:text-5xl">
              Your goals. Your food.{" "}
              <span className="text-gradient-accent">Your plan.</span>
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg text-[#A1A1AA]">
              Join thousands of people building sustainable fitness habits with the food they love.
              Start your free account today.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/onboarding"
                className="rounded-2xl bg-amber-500 px-10 py-4 text-base font-bold text-[#0A0A0A] transition hover:bg-amber-400"
              >
                Start Your Journey
              </Link>
              <Link
                href="/auth/login"
                className="rounded-2xl border border-white/10 bg-white/[0.03] px-8 py-4 text-base font-medium text-[#A1A1AA] transition-all hover:bg-white/[0.06] hover:text-[#FAFAFA]"
              >
                I already have an account
              </Link>
            </div>
          </AnimateIn>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 text-sm text-[#71717A] md:flex-row md:items-center md:justify-between">
          <p>© 2026 South Asian Fitness. Built with ❤️ for the diaspora.</p>
          <div className="flex flex-wrap gap-6">
            <Link href="/auth/login" className="transition hover:text-[#A1A1AA]">Login</Link>
            <Link href="/auth/signup" className="transition hover:text-[#A1A1AA]">Sign up</Link>
            <Link href="/privacy" className="transition hover:text-[#A1A1AA]">Privacy</Link>
            <Link href="/terms" className="transition hover:text-[#A1A1AA]">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
