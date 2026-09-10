"use client";

import { useEffect, useState } from "react";

const COOKIE_KEY = "saf_cookie_consent";

export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(COOKIE_KEY)) {
        setVisible(true);
      }
    } catch {
      /* localStorage blocked (SSR / private mode) */
    }
  }, []);

  const handleAccept = () => {
    try {
      localStorage.setItem(COOKIE_KEY, "accepted");
    } catch {
      /* ignore */
    }
    setVisible(false);
  };

  const handleDecline = () => {
    try {
      localStorage.setItem(COOKIE_KEY, "declined");
    } catch {
      /* ignore */
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6">
      <div className="mx-auto flex max-w-2xl flex-col items-start gap-4 rounded-2xl border border-stone-200 bg-white p-5 shadow-xl shadow-stone-900/5 backdrop-blur-xl dark:border-zinc-700 dark:bg-zinc-900/90 dark:shadow-black/30 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-stone-900 dark:text-zinc-100">
            We use cookies to improve your experience.
          </p>
          <p className="mt-1 text-xs leading-relaxed text-stone-500 dark:text-zinc-500">
            Essential cookies keep the app running. Analytics cookies help us
            understand how you use South Asian Fitness.{" "}
            <a
              href="/privacy"
              className="underline underline-offset-2 text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
            >
              Privacy Policy
            </a>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDecline}
            className="rounded-xl border border-stone-200 bg-stone-50 px-4 py-2 text-xs font-medium text-stone-600 transition-all hover:bg-stone-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700"
          >
            Decline
          </button>
          <button
            onClick={handleAccept}
            className="rounded-xl bg-emerald-600 px-5 py-2 text-xs font-semibold text-white shadow-sm shadow-emerald-600/20 transition-all hover:bg-emerald-700 hover:shadow-md active:scale-[0.97]"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
