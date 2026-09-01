"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { AnimateIn, StaggerIn } from "@/components/animate-in";
import { FeatureScroll } from "@/components/landing/feature-scroll";
import { PricingSection } from "@/components/landing/pricing-section";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const HeroScene = dynamic(
  () => import("@/components/3d/hero-scene").then((m) => m.HeroScene),
  { ssr: false },
);

/* ── Old Way vs FlexAI Bento Data ────────────────────────────────────── */

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
      // Parallax reveal for bento cards
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
    <div className="dark min-h-screen bg-[#09090b] text-[#f5f0e8] overflow-x-hidden">
      {/* ── Navigation ─────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.04] bg-[#09090b]/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#c4854c] to-[#e8a838] text-sm font-bold text-[#f5f0e8] shadow-lg shadow-[#c4854c]/20">
              <span className="relative z-10">SA</span>
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-[#c4854c] to-[#e8a838] opacity-50 blur-md" />
            </div>
            <p className="text-lg font-semibold text-[#f5f0e8]">South Asian Fitness</p>
          </div>
          <nav className="hidden items-center gap-8 text-sm font-medium text-zinc-400 md:flex">
            <a href="#features" className="transition hover:text-[#f5f0e8]">Features</a>
            <a href="#how-it-works" className="transition hover:text-[#f5f0e8]">How it works</a>
            <a href="#pricing" className="transition hover:text-[#f5f0e8]">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href="/auth/login"
              className="rounded-xl px-4 py-2 text-sm font-medium text-zinc-400 transition hover:text-[#f5f0e8]"
            >
              Log in
            </Link>
            <Link
              href="/auth/signup"
              className="rounded-xl bg-gradient-to-r from-[#c4854c] to-[#e8a838] px-5 py-2.5 text-sm font-semibold text-[#f5f0e8] shadow-lg shadow-[#c4854c]/20 transition-all hover:shadow-[#c4854c]/30 hover:brightness-110"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero Section ───────────────────────────────────────────────── */}
      <section className="relative flex min-h-screen items-center overflow-hidden">
        {/* 3D Background */}
        <HeroScene />

        {/* Gradient orbs */}
        <div className="absolute left-[-10%] top-[20%] h-[500px] w-[500px] rounded-full bg-[#c4854c]/5 blur-[150px]" />
        <div className="absolute bottom-[10%] right-[-5%] h-[400px] w-[400px] rounded-full bg-[#e8a838]/5 blur-[120px]" />

        {/* Content */}
        <div className="relative z-10 mx-auto max-w-6xl px-6 pt-32 pb-20 md:pt-40">
          <div className="max-w-3xl">
            <AnimateIn delay={0.2} y={20} blur={4}>
              <div className="inline-flex items-center gap-2 rounded-full border border-[#c4854c]/20 bg-[#c4854c]/10 px-4 py-1.5 text-sm font-medium text-[#d4a574] mb-8">
                <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-[#c4854c]" />
                AI-powered nutrition for South Asian cuisine
              </div>
            </AnimateIn>

            <AnimateIn delay={0.4} y={30} blur={6}>
              <h1 className="font-serif text-5xl font-bold leading-[1.1] tracking-tight md:text-7xl lg:text-8xl">
                Fitness that fits{" "}
                <span className="text-gradient-cardamom">your culture.</span>
                <br />
                <span className="text-zinc-500">Powered by AI.</span>
              </h1>
            </AnimateIn>

            <AnimateIn delay={0.6} y={25} blur={4}>
              <p className="mt-8 max-w-xl text-lg leading-relaxed text-zinc-400 md:text-xl">
                Generate personalized, macro-optimized South Asian meal plans in seconds.
                Stop sacrificing the food you love to hit your goals.
              </p>
            </AnimateIn>

            <AnimateIn delay={0.8} y={20} blur={3}>
              <div className="mt-10 flex flex-col gap-4 sm:flex-row">
                <Link
                  href="/onboarding"
                  className="group relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#c4854c] to-[#e8a838] px-8 py-4 text-center text-base font-bold text-white shadow-xl shadow-[#c4854c]/25 transition-all hover:shadow-[#c4854c]/40 hover:brightness-110"
                >
                  <span className="relative z-10">Start Your Journey</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-[#e8a838] to-[#c4854c] opacity-0 transition-opacity group-hover:opacity-100" />
                </Link>
                <a
                  href="#how-it-works"
                  className="flex items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.03] px-8 py-4 text-base font-medium text-zinc-300 transition-all hover:bg-white/[0.06] hover:text-white"
                >
                  See how it works →
                </a>
              </div>
            </AnimateIn>

            <AnimateIn delay={1.0} y={15} blur={2}>
              <div className="mt-12 flex flex-wrap gap-6 text-sm text-zinc-500">
                <span className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-[#c4854c]" />
                  198+ South Asian foods
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-[#e8a838]" />
                  Multi-country support
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-[#c25a3c]" />
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
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#c4854c]">
                The problem
              </p>
              <h2 className="mt-4 font-serif text-3xl font-bold text-[#f5f0e8] md:text-5xl">
                The old way doesn't work.
              </h2>
            </div>
          </AnimateIn>

          <div ref={bentoRef} className="grid gap-6 md:grid-cols-2">
            {/* Old Way */}
            <div className="space-y-4">
              <div className="mb-6 flex items-center gap-3">
                <span className="rounded-lg bg-[#c25a3c]/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-[#c25a3c]">
                  The old way
                </span>
                <div className="h-px flex-1 bg-[#c25a3c]/10" />
              </div>
              <StaggerIn stagger={0.1}>
                {oldWay.map((item) => (
                  <div
                    key={item.title}
                    data-bento
                    className="rounded-2xl border border-[#c25a3c]/10 bg-[#c25a3c]/[0.03] p-5"
                  >
                    <div className="flex items-start gap-4">
                      <span className="text-2xl">{item.icon}</span>
                      <div>
                        <h3 className="font-medium text-zinc-300">{item.title}</h3>
                        <p className="mt-1 text-sm text-zinc-500">{item.desc}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </StaggerIn>
            </div>

            {/* FlexAI Way */}
            <div className="space-y-4">
              <div className="mb-6 flex items-center gap-3">
                <span className="rounded-lg bg-[#c4854c]/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-[#c4854c]">
                  The FlexAI way
                </span>
                <div className="h-px flex-1 bg-[#c4854c]/10" />
              </div>
              <StaggerIn stagger={0.1} delay={0.2}>
                {flexAiWay.map((item) => (
                  <div
                    key={item.title}
                    data-bento
                    className="rounded-2xl border border-[#c4854c]/15 bg-[#c4854c]/[0.04] p-5 transition-all duration-500 hover:border-[#c4854c]/25 hover:bg-[#c4854c]/[0.07]"
                  >
                    <div className="flex items-start gap-4">
                      <span className="text-2xl">{item.icon}</span>
                      <div>
                        <h3 className="font-medium text-[#f5f0e8]">{item.title}</h3>
                        <p className="mt-1 text-sm text-zinc-400">{item.desc}</p>
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
          <div className="absolute left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#c4854c]/8 blur-[120px]" />
        </div>
        <div className="relative mx-auto max-w-3xl px-6 text-center">
          <AnimateIn>
            <h2 className="font-serif text-3xl font-bold text-[#f5f0e8] md:text-5xl">
              Your goals. Your food.{" "}
              <span className="text-gradient-cardamom">Your plan.</span>
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg text-zinc-400">
              Join thousands of people building sustainable fitness habits with the food they love.
              Start your free account today.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/onboarding"
                className="rounded-2xl bg-gradient-to-r from-[#c4854c] to-[#e8a838] px-10 py-4 text-base font-bold text-white shadow-xl shadow-[#c4854c]/25 transition-all hover:shadow-[#c4854c]/40 hover:brightness-110"
              >
                Start Your Journey
              </Link>
              <Link
                href="/auth/login"
                className="rounded-2xl border border-white/[0.08] bg-white/[0.03] px-8 py-4 text-base font-medium text-zinc-300 transition-all hover:bg-white/[0.06] hover:text-white"
              >
                I already have an account
              </Link>
            </div>
          </AnimateIn>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.04] py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 text-sm text-zinc-500 md:flex-row md:items-center md:justify-between">
          <p>© 2026 South Asian Fitness. Built with ❤️ for the diaspora.</p>
          <div className="flex flex-wrap gap-6">
            <Link href="/auth/login" className="transition hover:text-zinc-300">Login</Link>
            <Link href="/auth/signup" className="transition hover:text-zinc-300">Sign up</Link>
            <Link href="/privacy" className="transition hover:text-zinc-300">Privacy</Link>
            <Link href="/terms" className="transition hover:text-zinc-300">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
