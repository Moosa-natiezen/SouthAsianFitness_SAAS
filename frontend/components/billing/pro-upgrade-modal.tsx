"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { createCheckoutSession } from "@/lib/api";

/**
 * Global upgrade modal triggered by PRO_REQUIRED 403 errors.
 * Dark luxury glass aesthetic with neon accents.
 */
export function ProUpgradeModal() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleOpen = useCallback(() => {
    setOpen(true);
    setError(null);
  }, []);

  const handleClose = useCallback(() => {
    setOpen(false);
    setError(null);
  }, []);

  const handleUpgrade = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { checkout_url } = await createCheckoutSession();
      if (checkout_url) {
        window.location.href = checkout_url;
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to start checkout.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    window.addEventListener("pro-required", handleOpen);
    return () => window.removeEventListener("pro-required", handleOpen);
  }, [handleOpen]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-md overflow-hidden rounded-2xl glass-strong">
        {/* Glow accents */}
        <div className="absolute -left-20 -top-20 h-40 w-40 rounded-full bg-[#c4854c]/50/15 blur-[60px]" />
        <div className="absolute -bottom-20 -right-20 h-40 w-40 rounded-full bg-[#e8a838]/10 blur-[60px]" />

        <div className="relative p-8">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#c4854c] to-[#e8a838] text-sm">
                  ✨
                </div>
                <h2 className="text-xl font-bold text-white">Upgrade to Pro</h2>
              </div>
              <p className="mt-1 text-sm text-zinc-400">
                Unlock the full power of your fitness journey.
              </p>
            </div>
            <button
              onClick={handleClose}
              className="rounded-lg p-1.5 text-zinc-500 transition-colors hover:bg-white/[0.06] hover:text-zinc-300"
              aria-label="Close"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Pro perks */}
          <div className="mt-6 space-y-3">
            <PerkItem icon="🚀" text="Unlimited AI meal plan generations" />
            <PerkItem icon="📊" text="Advanced macro tracking & analytics" />
            <PerkItem icon="🎯" text="Custom nutrition targets & dietary profiles" />
            <PerkItem icon="💰" text="Priority support & early feature access" />
          </div>

          {/* Error */}
          {error && (
            <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="mt-6 flex gap-3">
            <button
              onClick={handleUpgrade}
              disabled={loading}
              className="flex-1 rounded-xl bg-gradient-to-r from-[#c4854c] to-[#e8a838] px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-[#c4854c]/20 transition-all hover:shadow-[#c4854c]/30 hover:brightness-110 disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Redirecting…
                </span>
              ) : (
                "Upgrade to Pro"
              )}
            </button>
            <button
              onClick={handleClose}
              className="rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm font-medium text-zinc-400 transition-all hover:bg-white/[0.06] hover:text-zinc-200"
            >
              Not now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function PerkItem({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-white/[0.04] bg-white/[0.02] px-4 py-3">
      <span className="text-lg">{icon}</span>
      <span className="text-sm text-zinc-300">{text}</span>
    </div>
  );
}
