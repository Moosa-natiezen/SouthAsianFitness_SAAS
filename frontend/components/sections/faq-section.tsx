"use client";

import { useState } from "react";

/* ── FAQ — Accordion Section ──────────────────────────────────── */

const faqs = [
  {
    question:
      "Are the meal plans entirely South Asian?",
    answer:
      "Yes. We generate authentic, macro-balanced Desi dishes — Biryani, Parathas, Daal, Karahi, Tikka, and more. Every meal in your plan comes from our 215+ South Asian food library with accurate macros per serving. No generic Western substitutes, ever.",
  },
  {
    question: "Do I need a gym membership?",
    answer:
      "No. Our AI workout generator customizes routines based on your available equipment — including full bodyweight-only programs. Whether you have a full gym, just dumbbells, or nothing at all, the plan adapts to what you have.",
  },
  {
    question:
      "Are vegetarian/vegan options available?",
    answer:
      "Absolutely. We include extensive plant-based proteins like Paneer, Lentils (Masoor, Moong, Chana), Tofu, and Chana Masala. During onboarding you can set dietary preferences and the AI will tailor every meal around them.",
  },
  {
    question: "Can I cancel my subscription anytime?",
    answer:
      "Yes, you can cancel your Pro subscription at any time from your account settings. Your access continues until the end of your current billing period. No cancellation fees, no questions asked.",
  },
  {
    question: "Is my health data private and secure?",
    answer:
      "Yes. Your data is stored with industry-standard encryption (bcrypt hashing, HttpOnly session cookies, CSRF protection, TLS in transit). We never sell or share your personal data. You can delete your account and all data at any time.",
  },
];

function FAQItem({
  question,
  answer,
}: {
  question: string;
  answer: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl border border-stone-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 overflow-hidden transition-all duration-200">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-6 py-5 text-left"
        aria-expanded={open}
      >
        <span className="text-sm font-semibold text-stone-900 dark:text-zinc-100 pr-4">
          {question}
        </span>
        <svg
          className={`h-5 w-5 flex-shrink-0 text-stone-400 dark:text-zinc-500 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m19.5 8.25-7.5 7.5-7.5-7.5"
          />
        </svg>
      </button>
      {open && (
        <div className="px-6 pb-5 text-sm leading-relaxed text-stone-500 dark:text-zinc-500">
          {answer}
        </div>
      )}
    </div>
  );
}

export function FAQSection() {
  return (
    <section className="py-28 md:py-36 bg-background">
      <div className="mx-auto max-w-3xl px-6">
        <div className="mb-14 text-center">
          <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-emerald-600">
            FAQ
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-stone-900 dark:text-zinc-100 md:text-4xl font-serif">
            Frequently asked questions.
          </h2>
        </div>
        <div className="space-y-4">
          {faqs.map((faq) => (
            <FAQItem
              key={faq.question}
              question={faq.question}
              answer={faq.answer}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
