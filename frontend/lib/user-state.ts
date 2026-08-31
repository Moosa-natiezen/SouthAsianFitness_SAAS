/**
 * Lightweight shared user state.
 *
 * Every page that calls getCurrentUser() should write the result here via
 * setUserState().  Components that need the current user can subscribe
 * via onUserStateChange() and will be notified whenever the value changes.
 *
 * This avoids prop-drilling and keeps the billing-tier polling in sync
 * across Dashboard, Settings, Meal-Plans, etc. without a full Context tree.
 */

import type { AuthUser } from "./api";

type Listener = (user: AuthUser | null) => void;

let currentUser: AuthUser | null = null;
const listeners = new Set<Listener>();

export function getUserState(): AuthUser | null {
  return currentUser;
}

export function setUserState(user: AuthUser | null): void {
  // Skip update if nothing changed (avoids re-render storms)
  if (
    currentUser !== null &&
    user !== null &&
    currentUser.id === user.id &&
    currentUser.subscription_tier === user.subscription_tier &&
    currentUser.is_onboarded === user.is_onboarded
  ) {
    return;
  }
  currentUser = user;
  for (const fn of listeners) {
    fn(user);
  }
}

export function onUserStateChange(fn: Listener): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}
