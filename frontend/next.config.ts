import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

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
