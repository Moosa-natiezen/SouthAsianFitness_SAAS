import { BackendStatus } from "@/components/backend-status";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-16">
      <div className="mb-8 max-w-md space-y-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">South Asian Fitness</h1>
        <p className="text-muted-foreground">
          Personalized, budget-friendly diet and fitness planning.
        </p>
      </div>
      <BackendStatus />
    </main>
  );
}
