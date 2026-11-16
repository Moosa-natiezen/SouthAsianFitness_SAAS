"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getStoredUtms, trackSignupIntent } from "@/lib/utm";

/* ── Google Identity Services typing ───────────────────────────────────── */

type GoogleCredentialResponse = { credential?: string };

type GoogleButtonOptions = {
  type?: "standard" | "icon";
  theme?: "outline" | "filled_blue" | "filled_black";
  size?: "large" | "medium" | "small";
  text?: "signin_with" | "signup_with" | "continue_with" | "signin";
  shape?: "rectangular" | "pill" | "circle" | "square";
  logo_alignment?: "left" | "center";
  width?: number;
};

type GoogleAccountsId = {
  initialize: (config: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
    ux_mode?: "popup" | "redirect";
    auto_select?: boolean;
    cancel_on_tap_outside?: boolean;
  }) => void;
  renderButton: (parent: HTMLElement, options: GoogleButtonOptions) => void;
};

type GoogleGIS = { accounts: { id: GoogleAccountsId } };

declare global {
  interface Window {
    google?: GoogleGIS;
  }
}

/* ── Constants ─────────────────────────────────────────────────────────── */

const initialState = {
  displayName: "",
  email: "",
  password: "",
};

/** Maximum time (ms) to wait for the Google Identity Services library to load */
const GIS_LOAD_TIMEOUT_MS = 8_000;
/** Maximum time (ms) to wait for the backend to exchange the Google ID token */
const GOOGLE_EXCHANGE_TIMEOUT_MS = 20_000;

const EMAIL_EXISTS_COPY =
  "An account with this email already exists. Please sign in instead.";

/* ── Error rendering ───────────────────────────────────────────────────── */

/** Read the HTTP status from an `ApiError` without statically importing lib/api. */
function errorStatus(error: unknown): number | undefined {
  if (typeof error === "object" && error !== null && "status" in error) {
    const value = (error as { status?: unknown }).status;
    if (typeof value === "number") return value;
  }
  return undefined;
}

/**
 * Turn any thrown auth error into copy a human can act on.
 *
 * The backend answers a duplicate signup with `409 {"detail": "Account already
 * exists."}`, login failures with `401`, schema problems with `422` (FastAPI's
 * validation array, already flattened to its first message by `apiFetch`) and
 * outages with `500`/`503` — every one of them must reach the form, never be
 * swallowed by a reset or redirect.
 */
function authErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  const raw = error instanceof Error ? error.message.trim() : "";
  const status = errorStatus(error);
  const normalized = raw.toLowerCase();

  if (
    status === 409 ||
    normalized.includes("account already exists") ||
    normalized.includes("email already registered") ||
    normalized.includes("email registered") ||
    normalized.includes("email_exists")
  ) {
    return EMAIL_EXISTS_COPY;
  }

  // Generic transport-level messages are replaced with actionable copy.
  if (!raw || raw.startsWith("Request failed with status")) {
    if (status === 400) return "We could not accept those details. Please review and try again.";
    if (status === 401) return "Incorrect email or password.";
    if (status === 409) return EMAIL_EXISTS_COPY;
    if (status === 422) return "Please check the details you entered and try again.";
    if (status === 429) return "Too many attempts. Please wait a few minutes and try again.";
    if (status === 503) return "Sign-in is temporarily unavailable. Please try again shortly.";
    if (status && status >= 500) return "The server hit an unexpected error. Please try again.";
    return fallback;
  }

  return raw;
}

/* ── Component ─────────────────────────────────────────────────────────── */

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryingLogin, setRetryingLogin] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Read once at render: Next inlines NEXT_PUBLIC_* at build time, so a missing
  // value means the deployment simply cannot talk to Google.
  const googleClientId = (process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "").trim();

  // "loading" until Identity Services is ready, then "ready" once the official
  // Google button is rendered, or "unavailable" if it could not be set up.
  const [googleStatus, setGoogleStatus] = useState<"loading" | "ready" | "unavailable">(
    googleClientId ? "loading" : "unavailable",
  );

  // Container that Google renders its own button into. The button Google
  // renders always opens the account chooser popup — unlike One Tap
  // (`accounts.id.prompt()`), which Chrome silently suppresses after a
  // dismissal, leaving our button spinning with nothing on screen.
  const googleButtonRef = useRef<HTMLDivElement | null>(null);
  const credentialHandlerRef = useRef<(credential: string) => void>(() => {});

  // Honeypot field (signup only). Left uncontrolled on purpose: the value is
  // only read at submit time from the DOM, so any bot that fills the field
  // programmatically is caught without triggering React re-renders.
  const honeypotRef = useRef<HTMLInputElement | null>(null);

  const isSignup = mode === "signup";

  const validate = () => {
    if (!form.email.trim()) {
      return "Email is required.";
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      return "Enter a valid email address.";
    }

    if (!form.password) {
      return "Password is required.";
    }

    if (form.password.length < 8) {
      return "Password must be at least 8 characters.";
    }

    if (isSignup && !form.displayName.trim()) {
      return "Display name is required.";
    }

    return null;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationError = validate();

    if (validationError) {
      setError(validationError);
      return;
    }

    // ── Bot protection: the honeypot is visually hidden, so only bots fill it.
    // Abort silently and fake a successful signup (redirect like a real
    // submission) without ever hitting the backend.
    if (isSignup && honeypotRef.current?.value) {
      console.warn("[auth] Honeypot field populated — signup request suppressed.");
      router.push("/onboarding");
      router.refresh();
      return;
    }

    setLoading(true);
    setError(null);
    setRetryingLogin(false);

    try {
      const { loginUser, registerUser } = await import("@/lib/api");

      if (isSignup) {
        // Attach marketing attribution captured on landing, and fire a
        // GA event so signups can be analyzed even without the DB columns.
        const utmParams = getStoredUtms();
        trackSignupIntent();
        await registerUser({
          email: form.email.trim(),
          password: form.password,
          display_name: form.displayName.trim(),
          ...utmParams,
        });
      } else {
        await loginUser(
          {
            email: form.email.trim(),
            password: form.password,
          },
          () => setRetryingLogin(true),
        );
      }

      router.push("/onboarding");
      router.refresh();
    } catch (caughtError) {
      // Stay on the form: the user must see why the attempt failed (duplicate
      // email, wrong password, validation) instead of being bounced away.
      setRetryingLogin(false);
      setError(authErrorMessage(caughtError, "Authentication failed. Please try again."));
    } finally {
      setLoading(false);
      setRetryingLogin(false);
    }
  };

  /* ── Google sign-in ──────────────────────────────────────────────────── */

  const handleGoogleCredential = useCallback(
    async (credential: string) => {
      setGoogleLoading(true);
      setError(null);

      try {
        const { apiBaseUrl } = await import("@/lib/api");
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), GOOGLE_EXCHANGE_TIMEOUT_MS);

        let response: Response;
        try {
          response = await fetch(`${apiBaseUrl}/api/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            credentials: "include",
            body: JSON.stringify({ id_token: credential }),
            signal: controller.signal,
          });
        } finally {
          clearTimeout(timeoutId);
        }

        if (!response.ok) {
          // Surface the backend's message (string detail, or the first entry of
          // FastAPI's validation array) instead of failing silently.
          let detail = "";
          try {
            const body = (await response.json()) as {
              detail?: string | Array<{ msg?: string }>;
            };
            if (typeof body.detail === "string") {
              detail = body.detail;
            } else if (Array.isArray(body.detail) && typeof body.detail[0]?.msg === "string") {
              detail = body.detail[0].msg;
            }
          } catch {
            // Non-JSON body — fall back to the status-based copy below.
          }

          if (detail === "EMAIL_EXISTS_WITH_PASSWORD") {
            setError(
              "An account with this email already exists using a password. " +
                "Please sign in with your email and password instead.",
            );
            return;
          }

          setError(
            authErrorMessage(
              Object.assign(new Error(detail), { status: response.status }),
              `Google sign-in failed (HTTP ${response.status}). Please try again.`,
            ),
          );
          return;
        }

        // Session cookies are set by the backend on the 200 response.
        router.push("/dashboard");
        router.refresh();
      } catch (caughtError) {
        if (caughtError instanceof DOMException && caughtError.name === "AbortError") {
          setError("Google sign-in timed out. Please try again.");
        } else {
          setError(authErrorMessage(caughtError, "Google sign-in failed. Please try again."));
        }
      } finally {
        setGoogleLoading(false);
      }
    },
    [router],
  );

  // Keep the callback Google holds a reference to pointing at the latest handler.
  useEffect(() => {
    credentialHandlerRef.current = (credential: string) => {
      void handleGoogleCredential(credential);
    };
  }, [handleGoogleCredential]);

  useEffect(() => {
    // Missing client ID is already reflected in the initial state above; the
    // button reports the misconfiguration when clicked instead of spinning.
    if (!googleClientId) {
      return;
    }

    let cancelled = false;
    let observer: ResizeObserver | null = null;

    const setup = async () => {
      try {
        const google = await loadGoogleIdentityServices(GIS_LOAD_TIMEOUT_MS);
        if (cancelled) return;

        const container = googleButtonRef.current;
        if (!container) {
          setGoogleStatus("unavailable");
          return;
        }

        google.accounts.id.initialize({
          client_id: googleClientId,
          // Popup mode: a real account-chooser window, never a suppressed One Tap.
          ux_mode: "popup",
          auto_select: false,
          cancel_on_tap_outside: true,
          callback: (response) => {
            if (response.credential) {
              credentialHandlerRef.current(response.credential);
            }
          },
        });

        const renderButton = () => {
          const width = Math.min(Math.max(container.clientWidth || 0, 220), 400);
          container.replaceChildren();
          google.accounts.id.renderButton(container, {
            type: "standard",
            theme: "outline",
            size: "large",
            text: "continue_with",
            shape: "rectangular",
            logo_alignment: "left",
            width,
          });
        };

        renderButton();
        setGoogleStatus("ready");

        // Google's iframe is a fixed pixel width — re-render when the card
        // resizes so the button never overflows on narrow phones.
        if (typeof ResizeObserver !== "undefined") {
          let lastWidth = container.clientWidth;
          observer = new ResizeObserver(() => {
            if ((container.clientWidth || 0) === lastWidth) return;
            lastWidth = container.clientWidth;
            renderButton();
          });
          observer.observe(container);
        }
      } catch (caughtError) {
        if (cancelled) return;
        console.error("[auth] Google Identity Services failed to initialise", caughtError);
        setGoogleStatus("unavailable");
      }
    };

    void setup();

    return () => {
      cancelled = true;
      observer?.disconnect();
    };
  }, [googleClientId]);

  const handleGoogleUnavailableClick = () => {
    // Never leave the button spinning: report why Google cannot start.
    setGoogleLoading(false);

    if (!googleClientId) {
      setError("Google Sign-In is not configured (missing NEXT_PUBLIC_GOOGLE_CLIENT_ID).");
      return;
    }

    if (googleStatus === "loading") {
      setError("Google Sign-In is still loading. Please try again in a moment.");
      return;
    }

    setError(
      "Google Sign-In could not be loaded. Please disable any script blocker and reload the page.",
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-stone-50 px-4 py-8 dark:bg-zinc-950">
      <Card className="w-full max-w-md border-stone-200 shadow-xl dark:border-zinc-800 dark:bg-zinc-900">
        <CardHeader>
          <CardTitle>{isSignup ? "Create your account" : "Welcome back"}</CardTitle>
          <CardDescription>
            {isSignup
              ? "Start your personalized fitness journey."
              : "Sign in to continue your plan."}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {/* Google OAuth — Google renders this button, which always opens the
              account chooser popup and hands back a credential ID token. */}
          <div className="relative">
            <div
              ref={googleButtonRef}
              className={
                googleStatus === "ready"
                  ? "flex min-h-[44px] w-full items-center justify-center"
                  : "hidden"
              }
            />

            {googleStatus !== "ready" ? (
              <button
                type="button"
                onClick={handleGoogleUnavailableClick}
                disabled={googleLoading}
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 transition-all duration-200 hover:bg-stone-50 hover:border-stone-300 active:scale-[0.98] disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 dark:hover:border-zinc-600"
              >
                {googleLoading ? (
                  <Spinner />
                ) : (
                  <GoogleGlyph />
                )}
                {googleLoading
                  ? "Connecting..."
                  : googleStatus === "loading"
                    ? "Loading Google…"
                    : "Continue with Google"}
              </button>
            ) : null}

            {googleLoading && googleStatus === "ready" ? (
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center gap-2 rounded-xl bg-white/85 text-sm font-medium text-stone-700 dark:bg-zinc-800/85 dark:text-zinc-200">
                <Spinner />
                Connecting...
              </div>
            ) : null}
          </div>

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-stone-200 dark:border-zinc-700" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-stone-400 dark:bg-zinc-900 dark:text-zinc-500">or continue with email</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {isSignup ? (
              // ── Honeypot: hidden from humans, irresistible to bots ──
              <input
                ref={honeypotRef}
                type="text"
                id="phone_number_extra"
                name="phone_number_extra"
                className="hidden"
                tabIndex={-1}
                autoComplete="off"
                aria-hidden="true"
              />
            ) : null}

            {isSignup ? (
              <div className="space-y-2">
                <label htmlFor="displayName" className="text-sm font-medium text-stone-500 dark:text-zinc-400">
                  Display name
                </label>
                <input
                  id="displayName"
                  name="displayName"
                  value={form.displayName}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, displayName: event.target.value }))
                  }
                  className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-stone-900 placeholder:text-stone-500 outline-none transition-all focus:border-amber-600 focus:ring-1 focus:ring-amber-600/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-amber-400 dark:focus:ring-amber-400/30"
                  placeholder="Your name"
                  autoComplete="name"
                />
              </div>
            ) : null}

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-stone-500 dark:text-zinc-400">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-stone-900 placeholder:text-stone-500 outline-none transition-all focus:border-amber-600 focus:ring-1 focus:ring-amber-600/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-amber-400 dark:focus:ring-amber-400/30"
                placeholder="you@example.com"
                autoComplete={isSignup ? "email" : "username"}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-stone-500 dark:text-zinc-400">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, password: event.target.value }))
                  }
                  className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 pr-10 text-stone-900 placeholder:text-stone-500 outline-none transition-all focus:border-amber-600 focus:ring-1 focus:ring-amber-600/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-amber-400 dark:focus:ring-amber-400/30"
                  placeholder="Enter an 8+ character password"
                  autoComplete={isSignup ? "new-password" : "current-password"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600 transition-colors dark:text-zinc-500 dark:hover:text-zinc-300"
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12c1.292 4.338 5.31 7.5 10.066 7.5.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {retryingLogin ? (
              <div
                role="status"
                className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300"
              >
                Waking up server, retrying...
              </div>
            ) : null}

            {error ? (
              <div
                role="alert"
                aria-live="polite"
                className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm font-medium text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300"
              >
                {error}
              </div>
            ) : null}

            <Button type="submit" className="w-full bg-amber-600 text-white hover:bg-amber-500 hover:shadow-md transition-all duration-200 dark:bg-amber-500 dark:text-amber-950 dark:hover:bg-amber-400 active:scale-[0.98]" disabled={loading}>
              {loading ? (isSignup ? "Creating account..." : "Signing in...") : isSignup ? "Create account" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-stone-500 dark:text-zinc-500">
            {isSignup ? "Already have an account?" : "Need an account?"}{" "}
            <Link href={isSignup ? "/auth/login" : "/auth/signup"} className="font-medium text-stone-900 hover:text-stone-900 dark:text-zinc-100 dark:hover:text-white">
              {isSignup ? "Log in" : "Sign up"}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

/* ── Pieces ────────────────────────────────────────────────────────────── */

function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function GoogleGlyph() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}

/* ── Google Identity Services loader ───────────────────────────────────── */

/**
 * Load the Google Identity Services library once and hand back the `google`
 * global. Reuses an existing script tag so re-mounts (React Strict Mode) never
 * inject a second copy, and always settles so the UI can never hang.
 */
function loadGoogleIdentityServices(timeoutMs = GIS_LOAD_TIMEOUT_MS): Promise<GoogleGIS> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined") {
      reject(new Error("Google Identity Services needs a browser"));
      return;
    }

    if (window.google?.accounts?.id) {
      resolve(window.google);
      return;
    }

    let settled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const finish = (action: () => void) => {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      action();
    };

    const handleLoad = () => {
      if (window.google?.accounts?.id) {
        finish(() => resolve(window.google as GoogleGIS));
      } else {
        finish(() => reject(new Error("Google Identity Services loaded but is unavailable")));
      }
    };

    timer = setTimeout(
      () => finish(() => reject(new Error("Google Identity Services timed out"))),
      timeoutMs,
    );

    const existing = document.querySelector<HTMLScriptElement>(
      'script[src="https://accounts.google.com/gsi/client"]',
    );

    if (existing) {
      existing.addEventListener("load", handleLoad);
      existing.addEventListener("error", () =>
        finish(() => reject(new Error("Failed to load Google Identity Services"))),
      );
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = handleLoad;
    script.onerror = () =>
      finish(() => reject(new Error("Failed to load Google Identity Services")));
    document.head.appendChild(script);
  });
}
