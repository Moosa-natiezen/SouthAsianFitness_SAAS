/* ── UTM attribution ──────────────────────────────────────────────────────
 * Marketing campaigns append ?utm_source=…&utm_medium=…&utm_campaign=… to
 * landing URLs. We capture those on first paint, persist them, and attach
 * them to the signup request so the backend can attribute registrations.
 * ---------------------------------------------------------------------- */

const UTM_STORAGE_KEY = "saf_utm_params";

/** Longest value we accept per parameter — keeps junk out of the DB. */
const MAX_UTM_LENGTH = 200;

const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign"] as const;

export type UtmKey = (typeof UTM_KEYS)[number];

export type UtmParams = Partial<Record<UtmKey, string>>;

function sanitize(raw: UtmParams): UtmParams {
  const clean: UtmParams = {};
  for (const key of UTM_KEYS) {
    const value = raw[key];
    if (typeof value === "string" && value.trim()) {
      clean[key] = value.trim().slice(0, MAX_UTM_LENGTH);
    }
  }
  return clean;
}

/**
 * Reads UTM parameters from a query string and persists them.
 * Safe to call on every route change — only writes storage when
 * parameters are actually present. Returns the captured params (if any).
 */
export function captureUtms(search: string = ""): UtmParams {
  if (typeof window === "undefined") return {};

  const effectiveSearch = search || window.location.search;
  if (!effectiveSearch) return {};

  const params = new URLSearchParams(effectiveSearch);
  const found: UtmParams = {};
  for (const key of UTM_KEYS) {
    const value = params.get(key);
    if (value) found[key] = value;
  }

  const clean = sanitize(found);
  if (Object.keys(clean).length === 0) return {};

  try {
    // sessionStorage scopes attribution to this browsing session;
    // localStorage mirrors it so returning visits keep the first touch.
    sessionStorage.setItem(UTM_STORAGE_KEY, JSON.stringify(clean));
    localStorage.setItem(UTM_STORAGE_KEY, JSON.stringify(clean));
  } catch {
    // Storage can be unavailable (private mode / blocked cookies) — non-fatal.
  }
  return clean;
}

/**
 * Returns the persisted UTM parameters, or {} when none were captured.
 * sessionStorage is preferred (most recent session); falls back to
 * localStorage for the original first-touch attribution.
 */
export function getStoredUtms(): UtmParams {
  if (typeof window === "undefined") return {};

  for (const store of [sessionStorage, localStorage]) {
    try {
      const raw = store.getItem(UTM_STORAGE_KEY);
      if (!raw) continue;
      const clean = sanitize(JSON.parse(raw) as UtmParams);
      if (Object.keys(clean).length > 0) return clean;
    } catch {
      // Corrupt entry — fall through to the next store.
    }
  }
  return {};
}

/**
 * Fire-and-forget Google Analytics event. No-ops when gtag is absent
 * (ad blockers, SSR, tests).
 */
export function trackGaEvent(action: string, params: Record<string, string> = {}): void {
  if (typeof window === "undefined") return;
  const gtag = (window as unknown as { gtag?: (...args: unknown[]) => void }).gtag;
  if (typeof gtag === "function") {
    gtag("event", action, params);
  }
}

/** Reports the signup intent (with attribution) to Google Analytics. */
export function trackSignupIntent(): void {
  trackGaEvent("sign_up_intent", { ...getStoredUtms() });
}
