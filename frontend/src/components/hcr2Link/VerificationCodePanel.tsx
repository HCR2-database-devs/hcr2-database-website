import { useEffect, useState } from "react";

import { generateHcr2VerificationCode } from "../../services/hcr2Link";
import type { Hcr2LinkCodeState } from "../../types/api";
import { CopyValueButton } from "./CopyValueButton";

type VerificationCodePanelProps = {
  codeState: Hcr2LinkCodeState | null;
  onCodeChanged: (state: Hcr2LinkCodeState) => void;
};

function formatCountdown(seconds: number): string {
  if (seconds <= 0) return "0s";
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return rest === 0 ? `${minutes}m` : `${minutes}m ${rest}s`;
}

/**
 * Shows the generated verification code and the reroll control.
 *
 * The countdown is cosmetic: the backend refuses a new code until the cooldown
 * has elapsed, so disabling the button is a courtesy rather than the
 * enforcement point. The censorship warning is deliberately prominent because
 * it is the single most common reason a verification fails.
 */
export function VerificationCodePanel({ codeState, onCodeChanged }: VerificationCodePanelProps) {
  const [now, setNow] = useState(() => Date.now());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // Both countdowns start from the seconds the server sent with this state
  // rather than from a client clock reading of a timestamp. The server is the
  // only party that knows the real elapsed time, and an integer is immune to
  // the timezone problem described in `parseServerDate`.
  const [reference, setReference] = useState(() => ({ at: Date.now(), expiresIn: 0, rerollIn: 0 }));

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const code = codeState?.code ?? null;

  useEffect(() => {
    if (!codeState) return;
    setReference({
      at: Date.now(),
      expiresIn: codeState.code_expires_in_seconds,
      rerollIn: codeState.reroll_available_in_seconds
    });
  }, [codeState?.code, codeState?.code_expires_in_seconds, codeState?.reroll_available_in_seconds, codeState]);

  const elapsed = Math.max(0, Math.round((now - reference.at) / 1000));
  const expiresIn = Math.max(0, reference.expiresIn - elapsed);
  const rerollIn = Math.max(0, reference.rerollIn - elapsed);
  const expired = code !== null && expiresIn === 0;
  const canReroll = rerollIn === 0 && !busy;

  async function reroll() {
    setBusy(true);
    setError("");
    try {
      const next = await generateHcr2VerificationCode();
      onCodeChanged(next);
      setNow(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate a new code.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="hcr2-code-panel">
      <p className="hcr2-code-warning">
        <strong>Read this before sending.</strong> If any part of the code or your player name
        gets replaced with <code>*</code> in team chat, reroll the code and try again. Make sure
        the full player name and code are visible before submitting your request.
      </p>

      {code ? (
        <>
          <div className="hcr2-code-value">
            <code>{code}</code>
            <CopyValueButton value={code} label="Copy full code" />
          </div>
          <p className={expired ? "hcr2-code-expired" : "hcr2-code-hint"}>
            {expired
              ? "This code has expired. Reroll it before sending it in team chat."
              : `This code expires in ${formatCountdown(expiresIn)}.`}
            {codeState?.code_roll_count ? ` Generated ${codeState.code_roll_count}x.` : ""}
          </p>
        </>
      ) : (
        <p className="frontend-muted">No code generated yet.</p>
      )}

      <div className="hcr2-code-actions">
        <button
          className="button"
          type="button"
          disabled={!canReroll}
          onClick={reroll}
        >
          {busy ? "Generating..." : code ? "Reroll code" : "Generate code"}
        </button>
        {!canReroll && !busy && rerollIn > 0 && (
          <span className="frontend-muted" role="timer" aria-live="polite">
            You can reroll in {formatCountdown(rerollIn)}
          </span>
        )}
      </div>

      {error && <p className="frontend-error">{error}</p>}

      <p className="form-hint">
        Send the complete code in the verification team&apos;s in-game chat. Rerolling
        immediately invalidates the previous code, so only the newest code is accepted.
      </p>
    </div>
  );
}