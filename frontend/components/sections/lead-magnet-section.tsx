"use client";

import { useState, type FormEvent } from "react";

/* ── Lead Magnet — Email Capture ───────────────────────────────── */

export function LeadMagnetSection() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    "idle",
  );
  const [errorMsg, setErrorMsg] = useState("");

  function isValidEmail(value: string) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    if (!isValidEmail(email)) {
      setStatus("error");
      setErrorMsg("Please enter a valid email address.");
      return;
    }

    setStatus("loading");
    setErrorMsg("");

    try {
      const res = await fetch("/api/lead-capture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.error || "Something went wrong. Please try again.");
      }

      setStatus("success");
      setEmail("");
    } catch (err: unknown) {
      setStatus("error");
      setErrorMsg(
        err instanceof Error ? err.message : "Something went wrong. Please try again.",
      );
    }
  }

  return (
    <section className="relative overflow-hidden bg-emerald-600 py-20 md:py-24">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(255,255,255,0.15)_0%,transparent_50%)]" />
      </div>

      <div className="relative mx-auto max-w-3xl px-6 text-center">
        <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-emerald-100/80">
          Free Resource
        </p>
        <h2 className="text-3xl font-semibold tracking-tight text-white md:text-4xl font-serif">
          Get the Free South Asian Macro &amp; Diet Cheat Sheet
        </h2>
        <p className="mt-4 text-lg text-emerald-50/80 max-w-xl mx-auto">
          Learn how to track roti, biryani, and curries without guessing your
          macros. Delivered instantly to your inbox.
        </p>

        {status === "success" ? (
          <div className="mt-8 inline-flex items-center gap-2 rounded-full bg-white/20 px-6 py-3 text-sm font-semibold text-white backdrop-blur-sm">
            <svg
              className="h-5 w-5"
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
            Success! Check your inbox.
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center"
          >
            <div className="w-full max-w-sm">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (status === "error") setStatus("idle");
                }}
                placeholder="Enter your email address..."
                className="w-full rounded-full bg-white px-5 py-3 text-sm text-stone-900 placeholder:text-stone-400 shadow-lg ring-1 ring-white/20 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all"
                disabled={status === "loading"}
              />
              {status === "error" && errorMsg && (
                <p className="mt-2 text-left text-xs text-emerald-100">
                  {errorMsg}
                </p>
              )}
            </div>
            <button
              type="submit"
              disabled={status === "loading"}
              className="inline-flex items-center gap-2 rounded-full bg-stone-900 px-7 py-3 text-sm font-semibold text-white shadow-lg transition-all duration-200 hover:bg-stone-800 hover:shadow-xl active:scale-[0.97] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {status === "loading" ? (
                <>
                  <svg
                    className="h-4 w-4 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Sending...
                </>
              ) : (
                "Get Free Cheat Sheet"
              )}
            </button>
          </form>
        )}

        <p className="mt-4 text-xs text-emerald-100/60">
          No spam. Unsubscribe anytime. We respect your inbox.
        </p>
      </div>
    </section>
  );
}
