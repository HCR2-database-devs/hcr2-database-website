import type { ReactNode } from "react";

export type WizardStepId = "select_player" | "choose_method" | "verify" | "summary";

const STEP_LABELS: Record<WizardStepId, string> = {
  select_player: "Choose player name",
  choose_method: "Choose method",
  verify: "Verify",
  summary: "Submit"
};

export type WizardStep = {
  id: WizardStepId;
  title: string;
  body: ReactNode;
};

type Hcr2LinkWizardProps = {
  steps: WizardStep[];
  currentIndex: number;
  onBack: () => void;
  onContinue: () => void;
  continueLabel: string;
  continueDisabled?: boolean;
  busy?: boolean;
  error: string;
  notice: string;
};

/**
 * Step shell for the linking wizard: a progress indicator, one step's body at a
 * time, and Back/Continue controls. Deliberately generic so the method-specific
 * steps only have to supply their content.
 */
export function Hcr2LinkWizard({
  steps,
  currentIndex,
  onBack,
  onContinue,
  continueLabel,
  continueDisabled = false,
  busy = false,
  error,
  notice
}: Hcr2LinkWizardProps) {
  const current = steps[currentIndex];

  return (
    <div className="hcr2-wizard">
      <ol className="hcr2-wizard-progress" aria-label="Linking progress">
        {steps.map((step, index) => {
          const state =
            index < currentIndex ? "done" : index === currentIndex ? "current" : "todo";
          return (
            <li
              key={step.id}
              className={`hcr2-wizard-progress-step is-${state}`}
              aria-current={state === "current" ? "step" : undefined}
            >
              <span className="hcr2-wizard-progress-marker" aria-hidden="true">
                {index + 1}
              </span>
              <span className="hcr2-wizard-progress-label">{STEP_LABELS[step.id]}</span>
            </li>
          );
        })}
      </ol>

      <section className="hcr2-wizard-panel" aria-labelledby={`hcr2-step-${current.id}`}>
        <h3 id={`hcr2-step-${current.id}`}>{current.title}</h3>
        {current.body}

        {notice && <p className="frontend-message">{notice}</p>}
        {error && <p className="frontend-error">{error}</p>}

        <div className="hcr2-wizard-actions">
          <button className="button-ghost" type="button" onClick={onBack} disabled={busy}>
            Back
          </button>
          <button
            className="button"
            type="button"
            onClick={onContinue}
            disabled={busy || continueDisabled}
          >
            {busy ? "Working..." : continueLabel}
          </button>
        </div>
      </section>
    </div>
  );
}