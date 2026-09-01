"use client";

import dynamic from "next/dynamic";

const LiquidBackgroundInner = dynamic(
  () => import("@/components/3d/liquid-background").then((m) => m.LiquidBackground),
  { ssr: false },
);

/**
 * Client-only wrapper for the WebGL LiquidBackground.
 * Next.js 16 forbids `ssr: false` in Server Components (layout.tsx),
 * so this thin client component isolates the dynamic import.
 */
export function LiquidBackgroundClient() {
  return <LiquidBackgroundInner />;
}
