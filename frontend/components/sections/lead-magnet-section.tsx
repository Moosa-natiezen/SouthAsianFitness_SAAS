"use client";

import { useState, type FormEvent } from "react";

/* ── Lead Magnet — Email Capture (dark zinc + amber system) ───── */

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
    <section className="relative overflow-hidden border-y border-zinc-800 bg-zinc-900 py-20 md:py-24">
      {/* Amber accent hairline + faint glow */}
      <div
        aria-hidden
        className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/60 to-transparent"
      />
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-64 w-[42rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/8 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-3xl px-6 text-center">
        <p className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-amber-400">
          Free Resource
        </p>
        <h2 className="font-serif text-3xl font-semibold tracking-tight text-zinc-50 md:text-4xl">
          Get the Free South Asian Macro &amp; Diet Cheat Sheet
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-lg text-zinc-400">
          Learn how to track roti, biryani, and curries without guessing your
          macros. Delivered instantly to your inbox.
        </p>

        {status === "success" ? (
          <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-6 py-3 text-sm font-semibold text-emerald-300">
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
                className="w-full rounded-full border border-zinc-800 bg-zinc-950 px-5 py-3 text-sm text-zinc-100 shadow-lg shadow-black/20 transition-all placeholder:text-zinc-500 focus:border-amber-500/60 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
                disabled={status === "loading"}
              />
              {status === "error" && errorMsg && (
                <p className="mt-2 text-left text-xs text-amber-300">{errorMsg}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={status === "loading"}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-7 py-3 text-sm font-semibold text-zinc-950 shadow-lg shadow-amber-500/25 transition-all duration-200 hover:shadow-xl hover:shadow-amber-500/40 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60"
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

        <p className="mt-4 text-xs text-zinc-500">
          No spam. Unsubscribe anytime. We respect your inbox.
        </p>
      </div>
    </section>
  );
}
