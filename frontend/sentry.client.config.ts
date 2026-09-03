import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV ?? "development",

    // Adjust this value in production, or use tracesSampler for greater control
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

    // Only allow Sentry in production or when DSN is set
    enabled: !!dsn,

    // Set sample rate for profiling — this is relative to tracesSampleRate
    profilesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,
  });
}
