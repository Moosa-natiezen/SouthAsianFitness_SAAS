"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { createCheckoutSession } from "@/lib/api";

/**
 * Global upgrade modal triggered by PRO_REQUIRED 403 errors.
 * Listens for the "pro-required" custom window event dispatched by apiFetch.
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-lg">Upgrade to Pro</CardTitle>
          <CardAction>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={handleClose}
              aria-label="Close"
            >
              ✕
            </Button>
          </CardAction>
        </CardHeader>

        <CardContent className="space-y-4">
          <CardDescription>
            This feature requires an active Pro subscription. Upgrade now to
            unlock unlimited meal plans, advanced analytics, and premium tools.
          </CardDescription>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex items-center gap-3">
            <Button onClick={handleUpgrade} disabled={loading}>
              {loading ? "Redirecting…" : "Upgrade to Pro"}
            </Button>
            <Button variant="ghost" onClick={handleClose}>
              Not now
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
