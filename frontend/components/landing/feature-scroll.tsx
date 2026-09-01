"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const SAMPLE_MEAL_PLAN = `## High-Protein Chicken Tikka Bowl

### Breakfast — Masala Omelette
- 3 egg whites + 1 whole egg
- Diced onion, tomato, green chili
- Fresh coriander, turmeric
- **Calories: 180 | Protein: 22g**

### Lunch — Chicken Tikka Rice Bowl
- 150g grilled chicken tikka (yogurt marinade)
- 1 cup brown basmati rice
- Cucumber raita, pickled onion
- **Calories: 520 | Protein: 42g**

### Dinner — Dal + Fish Curry
- 1 cup masoor dal
- 120g pomfret in turmeric-coconut sauce
- Steamed rice, sautéed spinach
- **Calories: 480 | Protein: 38g**

### Snack — Protein Lassi
- 200ml low-fat dahi
- 1 scoop whey protein
- Cardamom, ice
- **Calories: 190 | Protein: 28g**

---
**Daily Total: 1,370 kcal | Protein: 130g**
AI-generated • Customized for your goals`;

/**
 * FeatureScroll — GSAP ScrollTrigger typing animation.
 * As the user scrolls through this section, the sample meal plan
 * "types out" character by character, simulating the AI streaming effect.
 */
export function FeatureScroll() {
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLPreElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const textEl = textRef.current;
    const progressEl = progressRef.current;
    if (!container || !textEl || !progressEl) return;

    const ctx = gsap.context(() => {
      // Set up the text container height for scroll space
      const totalChars = SAMPLE_MEAL_PLAN.length;

      // Animate text reveal based on scroll progress
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: container,
          start: "top 80%",
          end: "bottom 20%",
          scrub: 1.5,
          onUpdate: (self) => {
            // Update progress bar
            gsap.set(progressEl, { scaleX: self.progress });
          },
        },
      });

      // Reveal characters progressively
      tl.fromTo(
        textEl,
        { clipPath: "inset(0 100% 0 0)" },
        { clipPath: "inset(0 0% 0 0)", duration: 1, ease: "none" },
      );
    }, container);

    return () => ctx.revert();
  }, []);

  return (
    <section className="relative py-24 md:py-32">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#FF4500]/5 blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-6xl px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-[#FF4500]">
            The AI in action
          </p>
          <h2 className="mt-4 font-serif text-3xl font-bold text-[#FFFFFF] md:text-5xl">
            Watch your plan come alive
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-[#94A3B8]">
            Real-time streaming. Real South Asian cuisine. Real macro precision.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-[1fr_1.2fr]">
          {/* Left: feature callouts */}
          <div className="flex flex-col justify-center gap-8">
            {[
              {
                num: "01",
                title: "Cultural Intelligence",
                desc: "Our AI understands South Asian cuisine — from dal tadka to biryani, every recommendation is rooted in your food traditions.",
              },
              {
                num: "02",
                title: "Macro Precision",
                desc: "Every meal is calculated to hit your protein, carb, and fat targets. No guesswork, no approximations.",
              },
              {
                num: "03",
                title: "Budget Aware",
                desc: "Plans adapt to your weekly grocery budget and local food prices across Pakistan, India, Bangladesh, and beyond.",
              },
            ].map((item, i) => (
              <div
                key={item.num}
                className="group relative rounded-2xl border border-white/8 bg-white/3 p-6 transition-all duration-500 hover:border-[#FF4500]/20 hover:bg-white/5"
              >
                <span className="font-serif text-4xl font-bold text-[#FF4500]/20 group-hover:text-[#FF4500]/40 transition-colors">
                  {item.num}
                </span>
                <h3 className="mt-2 text-lg font-semibold text-[#FFFFFF]">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#94A3B8]">{item.desc}</p>
              </div>
            ))}
          </div>

          {/* Right: streaming mock terminal */}
          <div ref={containerRef} className="relative min-h-[500px]">
            <div className="sticky top-24 overflow-hidden rounded-2xl border border-white/10 bg-[#0A0A12] shadow-2xl">
              {/* Terminal header */}
              <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
                <div className="h-3 w-3 rounded-full bg-[#FF4500]/60" />
                <div className="h-3 w-3 rounded-full bg-[#00E5FF]/60" />
                <div className="h-3 w-3 rounded-full bg-[#FF4500]/60" />
                <span className="ml-3 text-xs text-[#94A3B8]">AI Meal Generator</span>
                <span className="ml-auto flex items-center gap-1.5 text-xs text-[#FF4500]">
                  <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-[#FF4500]" />
                  streaming
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-0.5 bg-white/4">
                <div
                  ref={progressRef}
                  className="h-full origin-left bg-gradient-to-r from-[#FF4500] to-[#00E5FF]"
                  style={{ transform: "scaleX(0)" }}
                />
              </div>

              {/* Terminal content */}
              <pre
                ref={textRef}
                className="p-6 text-sm leading-relaxed text-[#CBD5E1] font-mono whitespace-pre-wrap"
              >
                {SAMPLE_MEAL_PLAN}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
