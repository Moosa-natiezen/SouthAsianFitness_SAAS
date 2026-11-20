import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

/**
 * Render origin for the FastAPI service.
 *
 * Set BACKEND_URL in the Vercel project when the service is renamed; the
 * fallback is the deployed API host already used by vercel.json.
 */
const backendUrl = (
  process.env.BACKEND_URL || "https://south-asian-fitness-api.onrender.com"
).replace(/\/+$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["three", "@react-three/fiber", "@react-three/drei"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
  async rewrites() {
    // /api/* belongs to the FastAPI backend, not to Next. Without this,
    // https://southasianfitness.com/api/health falls through to the Next 404
    // and uptime monitors/Render probes can never reach FastAPI. The
    // meal-plans/enqueue route is a Next API route (Trigger.dev) and must keep
    // being served locally, exactly as the vercel.json rewrite does.
    return [
      {
        source: "/api/health",
        destination: `${backendUrl}/api/health`,
      },
      {
        source: "/api/:path((?!meal-plans/enqueue).*)",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },

  async headers() {
    // Only headers NOT already set in vercel.json (which applies
    // X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and
    // Permissions-Policy at the edge). Keep each header in exactly one
    // place to avoid conflicting duplicates.
    return [
      {
        source: "/(.*)",
        headers: [
          // Force HTTPS for 2 years, including subdomains. Not "preload":
          // that requires HSTS preloading submission and is hard to undo.
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
          { key: "X-DNS-Prefetch-Control", value: "on" },
          { key: "X-Permitted-Cross-Domain-Policies", value: "none" },
        ],
      },
    ];
  },
};

export default withSentryConfig(nextConfig, {
  // Automatically tree-shake Sentry logger statements to reduce bundle size
  silent: true,
});
