"use client";

import { usePathname, useSearchParams } from "next/navigation";
import posthog from "posthog-js";
import { PostHogProvider as PHProvider, usePostHog } from "posthog-js/react";
import { Suspense, useEffect } from "react";

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
if (typeof window !== "undefined") {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://app.posthog.com";

  if (key) {
    try {
      posthog.init(key, {
        api_host: host,
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
