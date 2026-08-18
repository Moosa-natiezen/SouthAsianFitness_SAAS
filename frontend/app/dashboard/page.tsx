import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppShell } from "@/components/app-shell";

export default function DashboardPage() {
  return (
    <ProtectedRoute requireOnboarded={true}>
      <AppShell>
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.12em] text-emerald-700">Dashboard</p>
            <h2 className="mt-3 text-3xl font-semibold text-slate-900">Welcome back</h2>
            <p className="mt-2 max-w-2xl text-slate-600">
              Your personalized plan and progress tracking are getting started here.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Meal plans</p>
              <p className="mt-2 text-2xl font-semibold">Ready</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Food library</p>
              <p className="mt-2 text-2xl font-semibold">Growing</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Progress</p>
              <p className="mt-2 text-2xl font-semibold">On track</p>
            </div>
          </div>
        </div>
      </AppShell>
    </ProtectedRoute>
  );
}
