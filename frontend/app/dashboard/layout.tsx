import { AppShell } from "@/components/app-shell";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { DashboardProviders } from "@/components/dashboard/dashboard-providers";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute requireOnboarded={true}>
      <DashboardProviders>
        <AppShell>{children}</AppShell>
      </DashboardProviders>
    </ProtectedRoute>
  );
}
