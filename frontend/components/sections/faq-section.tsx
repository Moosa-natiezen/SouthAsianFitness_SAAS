"use client";

import { useState } from "react";

/* ── FAQ — Accordion Section ──────────────────────────────────── */

const faqs = [
  {
    question:
      "How does the app customize workouts and diets for South Asian lifestyles?",
    answer:
      "During onboarding, we collect your body stats (height, weight, age), activity level, fitness goals, dietary preferences, and cuisine type. Our TDEE engine uses the Mifflin-St Jeor equation to calculate your exact calorie and macro targets. The AI then generates meal plans using foods from our 215+ South Asian food library — so your plan includes foods like roti, daal, biryani, and karahi instead of generic Western meals.",
  },
  {
    question:
      "Can I track traditional foods like roti, biryani, and curries?",
    answer:
      "Absolutely. We have a searchable food library of 215+ pre-loaded South Asian dishes — including roti, paratha, biryani, butter chicken, daal chawal, paneer tikka, gulab jamun, and many more. Every dish includes accurate macros per standard serving. You can search by name, filter by category (curries, rice, breads, sweets), and log them directly to your daily meal plan.",
  },
  {
    question: "How does the subscription and billing work?",
    answer:
      "South Asian Fitness is free to start. The Free tier includes 3 AI meal plans per month, full access to the food library, and progress tracking. Pro ($9/month) unlocks unlimited AI meal plans, the AI workout generator, saved plans archive, and priority support. Billing is handled securely through Lemon Squeezy — we never see or store your payment information.",
  },
  {
    question: "Can I cancel my subscription anytime?",
    answer:
      "Yes, you can cancel your Pro subscription at any time from your account settings. Your access continues until the end of your current billing period. There are no cancellation fees and no questions asked. If you cancel, you'll be downgraded to the Free tier with all your data preserved.",
  },
  {
    question: "Is my health data private and secure?",
    answer:
      "Yes. Your profile and health data are stored securely with industry-standard encryption (bcrypt password hashing, HttpOnly session cookies, CSRF protection, TLS in transit). We never sell, share, or monetize your personal data. You can delete your account and all associated data at any time from the Settings page.",
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
