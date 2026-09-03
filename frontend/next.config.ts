import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["three", "@react-three/fiber", "@react-three/drei"],
};

export default withSentryConfig(nextConfig, {
  // Automatically tree-shake Sentry logger statements to reduce bundle size
  silent: true,
});
