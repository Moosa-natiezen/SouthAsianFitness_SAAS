import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV ?? "development",

    // Capture 100% of traces in development, 20% in production
    tracesSampleRate: process.env.NODE_ENV === "production" ? 0.2 : 1.0,

    // Session Replay — captures 100% of sessions on error, 10% otherwise
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    integrations: [
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],

    // Don't send PII
    sendDefaultPii: false,

    // Ensure all exception chains are captured
    normalizeDepth: 6,

    // Only allow Sentry when DSN is set
    enabled: !!dsn,

    // Profiling — relative to tracesSampleRate
    profilesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,

    // Capture console errors as breadcrumbs
    maxBreadcrumbs: 50,

    // Attach stack traces to all events
    attachStacktrace: true,
  });
}
