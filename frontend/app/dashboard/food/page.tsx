import { AppShell } from "@/components/app-shell";
import { ProtectedRoute } from "@/components/auth/protected-route";

export default function FoodPage() {
  return (
    <ProtectedRoute requireOnboarded={true}>
      <AppShell>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Food</h2>
          <p className="mt-2 text-slate-600">This area is reserved for food tracking and browsing.</p>
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}
