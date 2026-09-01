"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { loginUser, registerUser } from "@/lib/api";

const initialState = {
  displayName: "",
  email: "",
  password: "",
};

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#05050A] px-4 py-8">
      <Card className="w-full max-w-md border-white/10 shadow-xl">
        <CardHeader>
          <CardTitle>{isSignup ? "Create your account" : "Welcome back"}</CardTitle>
          <CardDescription>
            {isSignup
              ? "Start your personalized fitness journey."
              : "Sign in to continue your plan."}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            {isSignup ? (
              <div className="space-y-2">
                <label htmlFor="displayName" className="text-sm font-medium text-[#8A8A94]">
                  Display name
                </label>
                <input
                  id="displayName"
                  name="displayName"
                  value={form.displayName}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, displayName: event.target.value }))
                  }
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-white placeholder:text-[#8A8A94] outline-none transition-all focus:border-[#DC143C]/50 focus:ring-1 focus:ring-[#DC143C]/30"
                  placeholder="Your name"
                  autoComplete="name"
                />
              </div>
            ) : null}

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-[#8A8A94]">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-white placeholder:text-[#8A8A94] outline-none transition-all focus:border-[#DC143C]/50 focus:ring-1 focus:ring-[#DC143C]/30"
                placeholder="you@example.com"
                autoComplete={isSignup ? "email" : "username"}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-[#8A8A94]">
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
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-white placeholder:text-[#8A8A94] outline-none transition-all focus:border-[#DC143C]/50 focus:ring-1 focus:ring-[#DC143C]/30"
                placeholder="Enter an 8+ character password"
                autoComplete={isSignup ? "new-password" : "current-password"}
              />
            </div>

            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            ) : null}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (isSignup ? "Creating account..." : "Signing in...") : isSignup ? "Create account" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-[#8A8A94]">
            {isSignup ? "Already have an account?" : "Need an account?"}{" "}
            <Link href={isSignup ? "/auth/login" : "/auth/signup"} className="font-medium text-[#DC143C] hover:text-[#DC143C]">
              {isSignup ? "Log in" : "Sign up"}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
