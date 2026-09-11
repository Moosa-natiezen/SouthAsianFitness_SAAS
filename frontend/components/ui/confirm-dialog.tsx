"use client";

import { AlertDialog } from "@base-ui/react/alert-dialog";

import { cn } from "@/lib/utils";

/**
 * Accessible confirmation dialog for destructive actions, built on
 * Base UI's AlertDialog (focus trap, ESC handling, aria wiring included).
 *
 * Usage:
 *   <ConfirmDialog
 *     open={confirmOpen}
 *     onOpenChange={setConfirmOpen}
 *     onConfirm={handleLogout}
 *     title="Log out?"
 *     description="You'll need to sign in again to access your plan."
 *     confirmLabel="Log out"
 *   />
 */

export function ConfirmDialog({
  open,
  onOpenChange,
  onConfirm,
  title,
  description,
  confirmLabel = "Continue",
  cancelLabel = "Cancel",
  confirmDisabled = false,
  confirming = false,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmDisabled?: boolean;
  confirming?: boolean;
}) {
  const handleConfirm = () => {
    onConfirm();
    // The parent typically closes the dialog itself once its action
    // resolves; closing here guarantees dismissal for sync actions too.
    onOpenChange(false);
  };

  return (
    <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialog.Portal>
        <AlertDialog.Backdrop
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm transition-opacity duration-200"
          style={{ opacity: open ? 1 : 0 }}
        />
        <AlertDialog.Popup
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2",
            "rounded-2xl border border-stone-200 bg-white p-6 shadow-2xl outline-none",
            "dark:border-zinc-700 dark:bg-zinc-900",
          )}
        >
          <AlertDialog.Title className="text-lg font-semibold text-stone-900 dark:text-zinc-100">
            {title}
          </AlertDialog.Title>
          {description ? (
            <AlertDialog.Description className="mt-2 text-sm text-stone-500 dark:text-zinc-400">
              {description}
            </AlertDialog.Description>
          ) : null}

          <div className="mt-6 flex justify-end gap-3">
            <AlertDialog.Close
              className="rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm font-medium text-stone-600 transition-all duration-200 hover:bg-stone-100 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
              disabled={confirming}
            >
              {cancelLabel}
            </AlertDialog.Close>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={confirmDisabled || confirming}
              autoFocus
              className="rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-red-700 active:scale-[0.98] disabled:opacity-50 dark:bg-red-500 dark:hover:bg-red-400"
            >
              {confirming ? "Working..." : confirmLabel}
            </button>
          </div>
        </AlertDialog.Popup>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
