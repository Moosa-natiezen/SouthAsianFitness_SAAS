import type { Metadata } from "next";

import { AuthForm } from "@/components/auth/auth-form";

export const metadata: Metadata = {
  title: "Create account — South Asian Fitness",
  description:
    "Create your free account to get personalized, budget-friendly South Asian meal plans.",
};

export default function SignupPage() {
  return <AuthForm mode="signup" />;
}
