"use client";

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";

import {
  ApiError,
  clearCurrentUserCache,
  peekCurrentUser,
  refreshCurrentUser,
} from "@/lib/api";
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

    // Serve the last-known session immediately so switching sidebar tabs never
    // re-flashes the "Checking access..." gate, then verify with the server.
    const cachedUser = peekCurrentUser();
    if (cachedUser) {
      setUserState(cachedUser);
      setIsChecking(false);
      if (requireOnboarded && !cachedUser.is_onboarded) {
        router.replace("/onboarding");
        return;
      }
      if (!requireOnboarded && cachedUser.is_onboarded) {
        router.replace("/dashboard");
        return;
      }
    }

    const validateAccess = async () => {
      try {
        const currentUser = await refreshCurrentUser();

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
      } catch (err) {
        if (!isMounted) {
          return;
        }

        // Only a rejected session sends the user to login; a network blip must
        // not log them out now that the gate is no longer blocking.
        if (err instanceof ApiError && err.status === 401) {
          clearCurrentUserCache();
          router.replace("/auth/login");
        } else if (!cachedUser) {
          router.replace("/auth/login");
        }
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
        <div className="rounded-full border border-stone-200 bg-stone-50 px-4 py-2 text-sm font-medium text-stone-500">
          Checking access...
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
