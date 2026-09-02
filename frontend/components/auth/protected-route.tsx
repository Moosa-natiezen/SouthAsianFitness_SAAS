"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

import { getCurrentUser } from "@/lib/api";
import { setUserState } from "@/lib/user-state";

export function ProtectedRoute({
  children,
  requireOnboarded,
}: {
  children: ReactNode;
  requireOnboarded: boolean;
}) {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const validateAccess = async () => {
      try {
        const currentUser = await getCurrentUser();

        if (!isMounted) {
          return;
        }

        setUserState(currentUser);

        if (requireOnboarded && !currentUser.is_onboarded) {
          router.replace("/onboarding");
          return;
        }

        if (!requireOnboarded && currentUser.is_onboarded) {
          router.replace("/dashboard");
          return;
        }

        setIsChecking(false);
      } catch {
        if (!isMounted) {
          return;
        }

        router.replace("/auth/login");
      }
    };

    void validateAccess();

    return () => {
      isMounted = false;
    };
  }, [requireOnboarded, router]);

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a] px-4">
        <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-zinc-400">
          Checking access...
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
