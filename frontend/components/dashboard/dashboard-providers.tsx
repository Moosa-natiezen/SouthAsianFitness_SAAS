"use client";

import { ProUpgradeModal } from "@/components/billing/pro-upgrade-modal";

/**
 * Mounts global client-side providers for the dashboard.
 * Currently renders the ProUpgradeModal which listens for PRO_REQUIRED 403 events.
 */
export function DashboardProviders({ children }: { children: React.ReactNode }) {
  return (
    <>
      <ProUpgradeModal />
      {children}
    </>
  );
}
