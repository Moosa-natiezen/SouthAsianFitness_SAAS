import type { Metadata } from "next";

import { AuthForm } from "@/components/auth/auth-form";

export const metadata: Metadata = {
  title: "Log in — South Asian Fitness",
  description:
    "Sign in to access your personalized nutrition targets and meal plans.",
};

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
