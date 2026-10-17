import type { ReactNode } from "react";

type ClaimButtonProps = {
  /** Label shown before the user has claimed this step. */
  label: string;
  /** Label shown once claimed, while the step stays editable. */
  doneLabel: string;
  claimed: boolean;
  onClaim: () => void;
  busy?: boolean;
  /** Why the button is unavailable, shown as a hint beneath it. */
  blockedHint?: string;
  children?: ReactNode;
};

/**
 * A "I have done this" control.
 *
 * The site cannot verify any of these steps, so clicking only records the
 * user's statement. That makes silent buttons a real problem: a button that
 * changes nothing reads as broken, and a button that is enabled before its
 * prerequisite is met fails with a server error the user cannot act on. So the
 * control shows an explicit claimed state, disables itself with a visible
 * reason, and never pretends the underlying action was verified.
 */
export function ClaimButton({
  label,
  doneLabel,
  claimed,
  onClaim,
  busy = false,
  blockedHint,
  children
}: ClaimButtonProps) {
  return (
    <div className={`hcr2-claim${claimed ? " is-claimed" : ""}`}>
      <button
        className={claimed ? "button-ghost" : "button"}
        type="button"
        disabled={busy || claimed}
        aria-pressed={claimed}
        onClick={onClaim}
      >
        {claimed ? (
          <>
            <span className="hcr2-claim-check" aria-hidden="true">
              ✓
            </span>
            {doneLabel}
          </>
        ) : (
          label
        )}
      </button>
      {!claimed && blockedHint && <small className="form-hint">{blockedHint}</small>}
      {claimed && <small className="form-hint">Recorded as your statement. Admins confirm this themselves.</small>}
      {children}
    </div>
  );
}