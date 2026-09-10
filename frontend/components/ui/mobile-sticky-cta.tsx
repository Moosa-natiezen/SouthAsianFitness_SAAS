"use client";

import Link from "next/link";

/**
 * Fixed bottom CTA visible only on mobile (`max-md`).
 * Hidden on desktop to avoid competing with the nav CTA.
 */
export function MobileStickyCTA() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden print:hidden">
      <div className="mx-auto max-w-lg px-4 pb-4">
        <Link
          href="/auth/signup"
          className="flex items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-emerald-600/30 backdrop-blur transition-all duration-200 hover:bg-emerald-700 hover:shadow-xl active:scale-[0.97]"
        >
          Get Started — It&apos;s Free
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
