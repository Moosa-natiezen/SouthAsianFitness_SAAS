import type { Metadata } from "next";

import { AuthForm } from "@/components/auth/auth-form";

export const metadata: Metadata = {
  title: "Create account — South Asian Fitness",
  description:
    "Create your free account to get personalized, budget-friendly South Asian meal plans.",
  // Keep auth pages out of search results. robots.ts also disallows /auth/,
  // but robots.txt alone can't de-index an already-known URL — this directive
  // covers crawlers that reach the page by any other path.
  robots: { index: false, follow: false },
};

export default function SignupPage() {
  return <AuthForm mode="signup" />;
}
