import { AppShell } from "@/components/app-shell";
import { ProtectedRoute } from "@/components/auth/protected-route";

export default function SettingsPage() {
  return (
    <ProtectedRoute requireOnboarded={true}>
      <AppShell>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Settings</h2>
          <p className="mt-2 text-slate-600">This area is reserved for account and application settings.</p>
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}
