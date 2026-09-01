"use client";

import { ReactLenis } from "lenis/react";
import { type ReactNode } from "react";

/**
 * Wraps the app in Lenis for buttery-smooth scrolling.
 * Uses the React integration for automatic cleanup.
 */
export function LenisProvider({ children }: { children: ReactNode }) {
  return (
    <ReactLenis
      root
      options={{
        lerp: 0.1,
        duration: 1.2,
        smoothWheel: true,
      }}
    >
      {children}
    </ReactLenis>
  );
}
