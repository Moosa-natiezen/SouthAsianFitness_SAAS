import { AppShell } from "@/components/app-shell";
import { ProtectedRoute } from "@/components/auth/protected-route";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute requireOnboarded={true}>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  );
}
