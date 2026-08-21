import type { Metadata } from "next";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard";

export const metadata: Metadata = {
  title: "Set up your profile — South Asian Fitness",
  description:
    "Complete your profile to receive personalized nutrition and meal plan recommendations.",
};

export default function OnboardingPage() {
  return (
    <ProtectedRoute requireOnboarded={false}>
      <OnboardingWizard />
    </ProtectedRoute>
  );
}
