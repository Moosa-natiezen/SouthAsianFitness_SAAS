import Link from "next/link";

export const metadata = {
  title: "Page Not Found",
  // Keep the 404 out of search indexes explicitly.
  robots: { index: false, follow: true },
};

export default function NotFound() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[#FCFBF7] px-4 text-center">
      {/* Soft brand glows, matching the landing page aesthetic */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -left-24 h-72 w-72 rounded-full bg-emerald-600/10 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-emerald-600/10 blur-3xl"
      />

      <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-600 text-2xl font-bold text-white shadow-lg shadow-emerald-600/20">
        SA
      </div>

      <p className="mt-8 text-xs font-medium uppercase tracking-[0.25em] text-emerald-600">
        404 — Page not found
      </p>

      <h1 className="mt-3 max-w-xl text-4xl font-bold text-stone-900 md:text-5xl">
        This page isn&apos;t on the menu.
      </h1>

      <p className="mt-4 max-w-md text-lg text-stone-500">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
        Your macros are safe — let&apos;s get you back on track.
      </p>

      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <Link
          href="/"
          className="inline-flex items-center justify-center rounded-full bg-emerald-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-emerald-600/20 transition-all duration-200 hover:bg-emerald-700 hover:shadow-xl hover:shadow-emerald-600/30 active:scale-[0.97]"
        >
          Go to homepage
        </Link>
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center rounded-full border border-stone-200 bg-white px-8 py-3.5 text-sm font-semibold text-stone-900 shadow-sm transition-all duration-200 hover:border-emerald-600/40 hover:text-emerald-700 active:scale-[0.97]"
        >
          Go to dashboard
        </Link>
      </div>
    </div>
  );
}
