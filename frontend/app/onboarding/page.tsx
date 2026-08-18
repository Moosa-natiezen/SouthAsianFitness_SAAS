import { ProtectedRoute } from "@/components/auth/protected-route";
import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard";

export default function OnboardingPage() {
  return (
    <ProtectedRoute requireOnboarded={false}>
      <OnboardingWizard />
    </ProtectedRoute>
  );
}
