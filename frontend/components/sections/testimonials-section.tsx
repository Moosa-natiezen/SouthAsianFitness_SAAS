"use client";

/* ── Testimonials — Social Proof ──────────────────────────────── */

const testimonials = [
  {
    initials: "AP",
    name: "Ayesha P.",
    location: "Karachi → London",
    quote:
      "I've tried MyFitnessPal and LoseIt but none of them had proper South Asian foods. This app has Biryani, Karahi, Daal — everything my mom makes. I finally know how many calories are in my daily roti.",
  },
  {
    initials: "RK",
    name: "Rahul K.",
    location: "Delhi → Toronto",
    quote:
      "The AI meal generator is insane. I told it I want 180g protein on a budget, and it generated a full week of Pakistani meals — Chicken Karahi, Daal, Egg Bhurji. Saved me hours of planning.",
  },
  {
    initials: "FM",
    name: "Fatima M.",
    location: "Colombo → Melbourne",
    quote:
      "Lost 12kg in 3 months eating the food I grew up with. No more chicken breast and broccoli. This app understood that fitness doesn't mean giving up your culture.",
  },
];

function Stars() {
  return (
    <div className="mb-4 flex gap-0.5">
      {[...Array(5)].map((_, i) => (
        <svg
          key={i}
          className="h-4 w-4 text-emerald-600"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  );
}

export function TestimonialsSection() {
  return (
    <section className="bg-white dark:bg-zinc-900 py-28 md:py-36">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-16 md:mb-20 text-center">
          <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-emerald-600">
            Testimonials
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-stone-900 dark:text-zinc-100 md:text-4xl font-serif">
            Loved by the South Asian fitness community.
          </h2>
          <p className="mt-4 text-lg text-stone-500 dark:text-zinc-500 max-w-xl mx-auto">
            Real users. Real progress. Real food.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {testimonials.map((t) => (
            <div
              key={t.initials}
              className="rounded-3xl border border-stone-200 dark:border-zinc-700 bg-stone-50 dark:bg-zinc-800 p-8 card-hover"
            >
              <Stars />
              <p className="text-sm leading-relaxed text-stone-600 dark:text-zinc-400">
                &quot;{t.quote}&quot;
              </p>
              <div className="mt-6 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-sm font-bold text-white">
                  {t.initials}
                </div>
                <div>
                  <div className="text-sm font-semibold text-stone-900 dark:text-zinc-100">
                    {t.name}
                  </div>
                  <div className="text-xs text-stone-400 dark:text-zinc-500">
                    {t.location}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
