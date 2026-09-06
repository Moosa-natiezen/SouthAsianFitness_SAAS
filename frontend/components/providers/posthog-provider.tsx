"use client";

import { usePathname, useSearchParams } from "next/navigation";
import posthog from "posthog-js";
import { PostHogProvider as PHProvider, usePostHog } from "posthog-js/react";
import { Suspense, useEffect } from "react";

/**
 * TEMPORARY HARDCODE — requested for the Vercel production build.
 * The Vercel env vars were not inlining NEXT_PUBLIC_POSTHOG_KEY into the
 * client bundle, causing 404 config.js / 401 flags/ errors.
 *
 * NOTE: The PostHog project PUBLIC API key is safe to ship to the browser
 * (it is public by design — every client already receives it), so this is
 * not a credential leak. It is still a workaround:
 * TODO: revert to `process.env.NEXT_PUBLIC_POSTHOG_KEY` once the env var is
 * confirmed working in Vercel, so the key isn't duplicated in source control.
 */
const POSTHOG_KEY = "phc_AkJZgk2J6i6yEc7mspyZSNOnXxVduq5BN8WR4KrWvrs";
const POSTHOG_HOST =
  process.env.NEXT_PUBLIC_POSTHOG_HOST?.trim().replace(/\/+$/, "") ??
  "https://app.posthog.com";

/**
 * TEMPORARILY DISABLED — PostHog analytics paused to clean up production
 * console errors. Flip this to `true` to re-enable; no other changes needed.
 */
const POSTHOG_ENABLED = false;

/**
 * PostHog initialization — wrapped in try/catch so that 404/401 errors
 * from the config/flags API never block the main thread or crash the app.
 *
 * Key safeguards:
 * - `capture_pageview: false` — we handle this manually to avoid double-fires
 * - `disable_session_recording: true` — avoids extra /decide API calls
 * - `loaded` callback only runs debug in dev, no blocking operations
 * - Entire init is try/caught so a network failure is a silent no-op
 */
if (POSTHOG_ENABLED && typeof window !== "undefined") {
  // Safeguard debug log — presence only, NEVER the key value itself.
  // If this logs `false`, the hardcoded key was removed; previously this
  // flagged NEXT_PUBLIC_POSTHOG_KEY missing/stripped from the client bundle.
  console.log("PH Key present:", !!POSTHOG_KEY);

  if (POSTHOG_KEY) {
    try {
      posthog.init(POSTHOG_KEY, {
        api_host: POSTHOG_HOST,
        capture_pageview: false,
        capture_pageleave: true,
        persistence: "localStorage",
        // Disable session recording to reduce /decide and /slothd API calls
        // that can 401/404 and block the event loop
        disable_session_recording: true,
        loaded: () => {
          // Intentionally empty — no blocking operations here.
          // Debug mode is set via posthog.debug() only when explicitly needed.
        },
        // Silently swallow request errors so they never propagate to React
        on_request_error: () => {},
      });
    } catch {
      // PostHog init failed — silently continue. Analytics is non-critical.
    }
  } else {
    // Visible warning (not an error) so a misconfigured deployment is obvious
    // in the console without breaking the app.
    console.warn(
      "[posthog] POSTHOG_KEY is missing or invalid — analytics disabled."
    );
  }
}

function PostHogPageView() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const posthog = usePostHog();

  useEffect(() => {
    if (pathname && posthog) {
      let url = window.origin + pathname;
      if (searchParams.toString()) {
        url = url + `?${searchParams.toString()}`;
      }
      // Fire-and-forget — never block rendering on analytics
      try {
        posthog.capture("$pageview", { $current_url: url });
      } catch {
        // Silently ignore analytics failures
      }
    }
  }, [pathname, searchParams, posthog]);

  return null;
}

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  return (
    <PHProvider client={posthog}>
      <Suspense fallback={null}>
        <PostHogPageView />
      </Suspense>
      {children}
    </PHProvider>
  );
}
