"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useRef, useState } from "react";

/* eslint-disable @typescript-eslint/no-namespace */
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          prompt: () => void;
        };
      };
    };
  }
}
/* eslint-enable @typescript-eslint/no-namespace */

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const initialState = {
  displayName: "",
  email: "",
  password: "",
};

/** Maximum time (ms) to wait for the Google Identity Services library to load */
const GIS_LOAD_TIMEOUT_MS = 8_000;
/** Maximum time (ms) to wait for the user to select a Google account.
 *  Reduced from 60s to 15s — if the user dismisses the Google dialog
 *  without selecting, the button should reset quickly, not stay stuck
 *  on "Connecting..." for a full minute. */
const GOOGLE_PROMPT_TIMEOUT_MS = 15_000;

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refs to track timeouts so we can clean them up
  const googleTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const promptTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

    setLoading(true);
    setError(null);

    try {
      const { loginUser, registerUser } = await import("@/lib/api");

      if (isSignup) {
        await registerUser({
          email: form.email.trim(),
          password: form.password,
          display_name: form.displayName.trim(),
        });
      } else {
        await loginUser({
          email: form.email.trim(),
          password: form.password,
        });
      }

      router.push("/onboarding");
      router.refresh();
    } catch (caughtError) {
      const message =
        caughtError instanceof Error ? caughtError.message : "Authentication failed.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    // Prevent double-clicks
    if (googleLoading) return;

    setGoogleLoading(true);
    setError(null);

    try {
      // Load the Google Identity Services library with a timeout
      const google = await Promise.race([
        loadGoogleIdentityServices(),
        new Promise<never>((_, reject) => {
          googleTimeoutRef.current = setTimeout(
            () => reject(new Error("Google sign-in library timed out. Please try again.")),
            GIS_LOAD_TIMEOUT_MS,
          );
        }),
      ]);

      // Clear the load timeout since we succeeded
      if (googleTimeoutRef.current) {
        clearTimeout(googleTimeoutRef.current);
        googleTimeoutRef.current = null;
      }

      google.accounts.id.initialize({
        client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "",
        callback: async (response: { credential: string }) => {
          // Clear the prompt timeout since we got a response
          if (promptTimeoutRef.current) {
            clearTimeout(promptTimeoutRef.current);
            promptTimeoutRef.current = null;
          }

          const GOOGLE_TOKEN_EXCHANGE_TIMEOUT_MS = 10_000;

          try {
            const { apiBaseUrl } = await import("@/lib/api");

            // Race the token exchange against a 10s timeout so the UI
            // never freezes if the backend is unreachable or slow
            const controller = new AbortController();
            const timeoutId = setTimeout(
              () => controller.abort(),
              GOOGLE_TOKEN_EXCHANGE_TIMEOUT_MS,
            );

            let res: Response;
            try {
              res = await fetch(`${apiBaseUrl}/api/auth/google`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ id_token: response.credential }),
                signal: controller.signal,
              });
            } finally {
              clearTimeout(timeoutId);
            }

            if (!res.ok) {
              // Try to extract a meaningful error code from the backend
              let detail = "Google sign-in failed.";
              let errorCode = "";
              try {
                const errBody = await res.json();
                if (typeof errBody.detail === "string") {
                  detail = errBody.detail;
                  errorCode = errBody.detail;
                }
              } catch {
                // Ignore JSON parse failure — use the default message
              }

              // Special handling for email/password collision
              if (errorCode === "EMAIL_EXISTS_WITH_PASSWORD") {
                setError(
                  "An account with this email already exists using a password. " +
                  "Please log in with your email and password instead."
                );
                setGoogleLoading(false);
                return;
              }

              throw new Error(detail);
            }

            // The session cookie is set by the backend — navigate away
            await router.push("/dashboard");
            router.refresh();
          } catch (err) {
            if (err instanceof DOMException && err.name === "AbortError") {
              setError("Google sign-in timed out. Please try again.");
            } else {
              const message =
                err instanceof Error ? err.message : "Google sign-in failed.";
              setError(message);
            }
          } finally {
            setGoogleLoading(false);
          }
        },
      });

      // Show the Google One Tap prompt
      google.accounts.id.prompt();

      // Safety timeout — if the callback never fires (e.g. user dismissed
      // the Google dialog without selecting), reset the loading state so
      // the button doesn't stay stuck on "Connecting...".
      promptTimeoutRef.current = setTimeout(() => {
        setGoogleLoading(false);
      }, GOOGLE_PROMPT_TIMEOUT_MS);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load Google sign-in.";
      setError(message);
      setGoogleLoading(false);
    } finally {
      // Always clean up the load timeout
      if (googleTimeoutRef.current) {
        clearTimeout(googleTimeoutRef.current);
        googleTimeoutRef.current = null;
      }
    }
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
          {/* Google OAuth Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={googleLoading}
            className="flex w-full items-center justify-center gap-3 rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 transition-all duration-200 hover:bg-stone-50 hover:border-stone-300 active:scale-[0.98] disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 dark:hover:border-zinc-600"
          >
            {googleLoading ? (
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
            )}
            {googleLoading ? "Connecting..." : "Continue with Google"}
          </button>

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
                  className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-stone-900 placeholder:text-stone-500 outline-none transition-all focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-emerald-400 dark:focus:ring-emerald-400/30"
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
                className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-stone-900 placeholder:text-stone-500 outline-none transition-all focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-emerald-400 dark:focus:ring-emerald-400/30"
                placeholder="you@example.com"
                autoComplete={isSignup ? "email" : "username"}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-stone-500 dark:text-zinc-400">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                value={form.password}
                onChange={(event) =>
                  setForm((current) => ({ ...current, password: event.target.value }))
                }
                className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3.5 py-2.5 text-stone-900 placeholder:text-stone-500 outline-none transition-all focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-emerald-400 dark:focus:ring-emerald-400/30"
                placeholder="Enter an 8+ character password"
                autoComplete={isSignup ? "new-password" : "current-password"}
              />
            </div>

            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
                {error}
              </div>
            ) : null}

            <Button type="submit" className="w-full bg-emerald-600 text-white hover:bg-emerald-700 dark:bg-emerald-500 dark:text-emerald-950 dark:hover:bg-emerald-400" disabled={loading}>
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

/**
 * Dynamically load Google Identity Services (GIS) library.
 * Returns the `google` global with `accounts.id` API.
 * Wrapped in try/catch so network failures never propagate.
 */
type GoogleGIS = {
  accounts: {
    id: {
      initialize: (config: {
        client_id: string;
        callback: (response: { credential: string }) => void;
      }) => void;
      prompt: () => void;
    };
  };
};

function loadGoogleIdentityServices(): Promise<GoogleGIS> {
  return new Promise((resolve, reject) => {
    if (typeof window !== "undefined" && window.google?.accounts?.id) {
      resolve(window.google as GoogleGIS);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (window.google?.accounts?.id) {
        resolve(window.google as GoogleGIS);
      } else {
        reject(new Error("Google Identity Services loaded but not available"));
      }
    };
    script.onerror = () => reject(new Error("Failed to load Google Identity Services"));
    document.head.appendChild(script);
  });
}
