import { useEffect, useState } from "react";
import type { ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { BetaBadge } from "../BetaBadge";
import { formatMemberSince } from "../../lib/format";
import {
  cancelHcr2LinkRequest,
  chooseHcr2LinkMethod,
  confirmHcr2CodeSent,
  confirmHcr2ContactedOwner,
  confirmHcr2DiscordJoined,
  confirmHcr2DiscordReady,
  confirmHcr2TeamJoined,
  getHcr2LinkConfig,
  getHcr2LinkStatus,
  startHcr2LinkRequest,
  submitHcr2ChallengeLink,
  submitHcr2LinkRequest,
  unlinkHcr2Player
} from "../../services/hcr2Link";
import type {
  Hcr2LinkCodeState,
  Hcr2LinkConfig,
  Hcr2LinkMethod,
  Hcr2LinkPlayerOption,
  Hcr2LinkRequest
} from "../../types/api";
import { ClaimButton } from "./ClaimButton";
import { CopyValueButton } from "./CopyValueButton";
import { Hcr2LinkWizard, type WizardStep } from "./Hcr2LinkWizard";
import { PlayerNamePicker } from "./PlayerNamePicker";
import { VerificationCodePanel } from "./VerificationCodePanel";

const STATUS_LABELS: Record<string, string> = {
  draft: "Not started",
  in_progress: "In progress",
  submitted: "Submitted for admin review",
  approved: "Approved",
  rejected: "Rejected",
  expired: "Expired",
  cancelled: "Cancelled"
};

const REJECTION_LABELS: Record<string, string> = {
  code_not_visible: "the code or your player name was censored in team chat",
  wrong_player_name: "the wrong player name was linked",
  could_not_confirm_account: "we could not confirm the account",
  screen_share_inconclusive: "the screen share was inconclusive",
  challenge_mismatch: "your challenge link did not match the distance we assigned",
  name_already_linked: "that player name is already linked",
  no_contact: "we could not reach you",
  request_cancelled: "the request was cancelled",
  other: "please contact staff"
};

/** Shown on the summary step, so the member sees the same wording they picked. */
const METHOD_LABELS: Record<Hcr2LinkMethod, string> = {
  team: "A. Join the verification team",
  discord_screen_share: "B. Discord screen-share",
  playhcr_challenge: "C. Jeep distance challenge"
};

const VERIFY_STEP_TITLES: Record<Hcr2LinkMethod, string> = {
  team: "Join the verification team and send your code",
  discord_screen_share: "Arrange your Discord screen-share",
  playhcr_challenge: "Drive your distance and send the challenge link"
};

type LinkedHcr2AccountSectionProps = {
  communityUsername?: string | null;
  discordUsername?: string | null;
};

/** Map the server's stored step onto the four visible wizard steps. */
function stepIndexFor(request: Hcr2LinkRequest | null): number {
  if (!request) return 0;
  if (request.status === "submitted" || request.status === "approved") return 3;
  if (request.step === "select_player") return 0;
  if (request.step === "choose_method") return 1;
  // team_join / team_code / team_sent, the discord_* steps and the challenge_*
  // steps all live inside the single "verify" step.
  return 2;
}

export function LinkedHcr2AccountSection({
  communityUsername,
  discordUsername
}: LinkedHcr2AccountSectionProps) {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<Hcr2LinkPlayerOption | null>(null);
  const [nameConfirmed, setNameConfirmed] = useState(false);
  const [visibilityConfirmed, setVisibilityConfirmed] = useState(false);
  const [instructionsFollowed, setInstructionsFollowed] = useState(false);
  const [codeState, setCodeState] = useState<Hcr2LinkCodeState | null>(null);
  const [challengeUrl, setChallengeUrl] = useState("");
  const [stepOverride, setStepOverride] = useState<number | null>(null);
  const [restarting, setRestarting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const configQuery = useQuery({
    queryKey: ["hcr2-link", "config"],
    queryFn: getHcr2LinkConfig,
    staleTime: 5 * 60_000
  });

  const statusQuery = useQuery({
    queryKey: ["hcr2-link", "status"],
    queryFn: getHcr2LinkStatus,
    staleTime: 15_000
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["hcr2-link"] });

  const action = useMutation({
    mutationFn: (run: () => Promise<unknown>) => run(),
    onSuccess: async () => {
      setError("");
      await refresh();
    },
    onError: (actionError) => {
      setError(actionError instanceof Error ? actionError.message : "Request failed.");
    }
  });

  const link = statusQuery.data?.link ?? null;
  const config: Hcr2LinkConfig | undefined = configQuery.data;

  // `request` is the most recent attempt; `liveRequest` is the one the wizard
  // may actually work with. After an admin revokes a link the latest attempt is
  // still `approved`, and treating that as resumable is what made "Start a new
  // request" look broken: the picker refused to open because a finished request
  // was still supplying a player name.
  const request = statusQuery.data?.request ?? null;
  const liveRequest = statusQuery.data?.request_is_live ? request : null;

  // Adopt the server's position when the request *identity* changes, so leaving
  // and returning resumes correctly. Keyed on the id alone: keying it on
  // `step`/`status` made the wizard snap backwards after every Continue, which
  // issues a request that advances the stored step.
  useEffect(() => {
    setStepOverride(null);
    setRestarting(false);
  }, [request?.id]);

  // Seed the code panel from an existing code, e.g. after a reload. Separate
  // from the step logic so generating a code never disturbs navigation.
  useEffect(() => {
    setCodeState((previous) => {
      const code = liveRequest?.code;
      if (code && previous?.code !== code) {
        return {
          code,
          code_expires_at: liveRequest?.code_expires_at,
          code_expired: false,
          code_expires_in_seconds: 0,
          reroll_available_in_seconds: 0,
          reroll_cooldown_seconds: config?.code_reroll_cooldown_seconds ?? 10,
          code_roll_count: liveRequest?.code_roll_count ?? 0
        };
      }
      return previous;
    });
  }, [
    liveRequest?.code,
    liveRequest?.code_expires_at,
    liveRequest?.code_roll_count,
    config?.code_reroll_cooldown_seconds
  ]);

  // Seed the challenge link from an existing submission, e.g. after a reload,
  // so the member does not have to dig the link out again to change it.
  useEffect(() => {
    setChallengeUrl(liveRequest?.challenge_url ?? "");
  }, [liveRequest?.challenge_url]);

  const stepIndex = stepOverride ?? stepIndexFor(liveRequest);
  const busy = action.isPending;

  const teamComplete = Boolean(
    liveRequest?.team_joined_claimed && liveRequest?.code && liveRequest?.code_sent_claimed
  );
  const discordComplete = Boolean(
    liveRequest?.discord_joined_claimed && liveRequest?.contacted_owner_claimed
  );
  // The assigned distance is part of completion: without it there is nothing to
  // do the challenge for, and the backend refuses to submit in that state.
  const challengeComplete = Boolean(
    liveRequest?.challenge_distance_m && liveRequest?.challenge_link_claimed
  );
  const methodComplete =
    liveRequest?.verification_method === "team"
      ? teamComplete
      : liveRequest?.verification_method === "playhcr_challenge"
        ? challengeComplete
        : discordComplete;

  const method = liveRequest?.verification_method ?? null;
  const challengeDistance = liveRequest?.challenge_distance_m ?? null;
  const challengePrefix = config?.challenge.link_prefix ?? "";

  function beginFreshRequest() {
    setRestarting(true);
    setStepOverride(0);
    setSelected(null);
    setNameConfirmed(false);
    setVisibilityConfirmed(false);
    setInstructionsFollowed(false);
    setCodeState(null);
    setChallengeUrl("");
    setError("");
    setNotice("");
  }

  function claim(run: () => Promise<unknown>, message: string) {
    setError("");
    setNotice("");
    action.mutate(
      () =>
        run().then(() => {
          setNotice(message);
        })
    );
  }

  // ---------------------------------------------------------------- steps

  const selectStep: WizardStep = {
    id: "select_player",
    title: "Choose your HCR2 player name",
    body: (
      <div className="hcr2-step-body">
        <p>
          Search for the exact player name you want to link. Only names that appear in the records
          database are listed.
        </p>
        <PlayerNamePicker
          value={selected?.name_player ?? null}
          onSelect={(player) => {
            setSelected(player);
            setNameConfirmed(false);
          }}
          disabled={busy}
        />
        {selected && (
          <div className="hcr2-confirm-row">
            <p className="hcr2-confirm-question">
              Confirm this is the player name you want to link: <strong>{selected.name_player}</strong>
            </p>
            <label className="hcr2-inline-check">
              <input
                type="checkbox"
                checked={nameConfirmed}
                onChange={(event) => setNameConfirmed(event.target.checked)}
              />
              Yes, this is my player name
            </label>
            <p className="form-hint">
              Linking confirms you control the player name shown here at the time of verification.
              It does not verify your real-world identity, and it does not claim ownership of every
              historical record that matches this name.
            </p>
          </div>
        )}
      </div>
    )
  };

  const methodStep: WizardStep = {
    id: "choose_method",
    title: "Choose how you want to verify",
    body: (
      <div className="hcr2-method-cards">
        <article className="hcr2-method-card">
          <h4>A. Join the verification team</h4>
          <ul className="hcr2-method-list">
            <li>You must leave your current team to do this.</li>
            <li>Does not work with the Chinese version of HCR2.</li>
            <li>You will join the Hcr2 team we created and send a generated code in its in-game chat.</li>
            <li>An administrator reviews your request manually.</li>
          </ul>
          {config?.team.available ? (
            <button
              className="button"
              type="button"
              disabled={busy}
              onClick={() => claim(() => chooseHcr2LinkMethod("team"), "Verification team selected.")}
            >
              Use this method
            </button>
          ) : (
            <>
              <button className="button" type="button" disabled>
                Not configured yet
              </button>
              <small className="form-hint">
                The verification team has not been set up yet. Please contact staff if you need
                this method.
              </small>
            </>
          )}
        </article>

        <article className="hcr2-method-card">
          <h4>B. Discord screen-share</h4>
          <ul className="hcr2-method-list">
            <li>Join our Discord server using the invite link.</li>
            <li>
              DM {config?.discord.owner_handles.join(" or ") || "the site owner"} to arrange a time.
            </li>
            <li>In the call, share your screen showing your HCR2 account and the player name.</li>
            <li>
              <strong>You do not need a microphone and you do not need to speak.</strong>{" "}
              Screen-sharing is enough.
            </li>
            <li>An administrator reviews your request manually.</li>
          </ul>
          {config?.discord.available ? (
            <button
              className="button"
              type="button"
              disabled={busy}
              onClick={() =>
                claim(() => chooseHcr2LinkMethod("discord_screen_share"), "Discord screen-share selected.")
              }
            >
              Use this method
            </button>
          ) : (
            <>
              <button className="button" type="button" disabled>
                Not configured yet
              </button>
              <small className="form-hint">
                The Discord invite has not been set up yet. Please contact staff.
              </small>
            </>
          )}
        </article>

        <article className="hcr2-method-card">
          <h4>C. Jeep distance challenge</h4>
          <ul className="hcr2-method-list">
            <li>
              We pick a random distance between{" "}
              {config?.challenge.min_distance_m ?? 1} and{" "}
              {config?.challenge.max_distance_m ?? 2000} m. You cannot choose or re-roll it.
            </li>
            <li>Drive that distance with a jeep in Countryside Adventure.</li>
            <li>
              Create challenge about run and send the link to it.
            </li>
            <li>An administrator opens your challenge and checks your driver profile.</li>
          </ul>
          {config?.challenge.available ? (
            <button
              className="button"
              type="button"
              disabled={busy}
              onClick={() =>
                claim(
                  () => chooseHcr2LinkMethod("playhcr_challenge"),
                  "Challenge method selected. Your distance is assigned below."
                )
              }
            >
              Use this method
            </button>
          ) : (
            <>
              <button className="button" type="button" disabled>
                Not configured yet
              </button>
              <small className="form-hint">
                The challenge method has not been set up yet. Please contact staff if you need it.
              </small>
            </>
          )}
        </article>
      </div>
    )
  };

  const teamVerifyBody = (
    <div className="hcr2-step-body">
      <section className="hcr2-team-details">
        <h4>1. Join the verification team</h4>
        {config?.team.team_name ? (
          <>
            <div className="hcr2-detail-row">
              <span className="hcr2-detail-label">Team name</span>
              <strong>{config.team.team_name}</strong>
              <CopyValueButton value={config.team.team_name} label="Copy" />
            </div>
            {config.team.team_password && (
              <div className="hcr2-detail-row">
                <span className="hcr2-detail-label">Team password</span>
                <strong>{config.team.team_password}</strong>
                <CopyValueButton value={config.team.team_password} label="Copy" />
              </div>
            )}
            {config.team.details && <p className="frontend-muted">{config.team.details}</p>}
          </>
        ) : (
          <p className="frontend-muted">The verification team has not been set up yet.</p>
        )}
        <div className="hcr2-warn-stack">
          <p className="hcr2-warn">
            Leave your current team before joining the verification team.
          </p>
          <p className="hcr2-warn">This method does not work with the Chinese version of HCR2.</p>
        </div>
      </section>

      <ClaimButton
        label="I've joined the verification team"
        doneLabel="Joined the verification team"
        claimed={Boolean(liveRequest?.team_joined_claimed)}
        busy={busy}
        onClaim={() => claim(() => confirmHcr2TeamJoined(), "Thanks. Generate your code below.")}
      />

      {liveRequest?.team_joined_claimed && (
        <section className="hcr2-verify-section">
          <h4>2. Send your code in team chat</h4>
          <VerificationCodePanel codeState={codeState} onCodeChanged={setCodeState} />
          <label className="hcr2-inline-check">
            <input
              type="checkbox"
              checked={visibilityConfirmed}
              onChange={(event) => setVisibilityConfirmed(event.target.checked)}
            />
            The full player name and code were visible in team chat, with no asterisks
          </label>
          <ClaimButton
            label="I've sent the code in team chat"
            doneLabel="Code sent to team chat"
            claimed={Boolean(liveRequest?.code_sent_claimed)}
            busy={busy}
            blockedHint={!visibilityConfirmed ? "Tick the box above first." : undefined}
            onClaim={() =>
              claim(() => confirmHcr2CodeSent(visibilityConfirmed), "Thanks. Continue to submit your request.")
            }
          />
        </section>
      )}
    </div>
  );

  const discordVerifyBody = (
    <div className="hcr2-step-body">
      <section className="hcr2-verify-section">
        <h4>1. Join our Discord server</h4>
        {config?.discord.invite_url ? (
          <a
            className="button"
            href={config.discord.invite_url}
            target="_blank"
            rel="noreferrer noopener"
          >
            Open the Discord invite
          </a>
        ) : (
          <p className="frontend-muted">The invite link has not been set up yet.</p>
        )}
        <ClaimButton
          label="I've joined the server"
          doneLabel="Joined the Discord server"
          claimed={Boolean(liveRequest?.discord_joined_claimed)}
          busy={busy}
          onClaim={() => claim(() => confirmHcr2DiscordJoined(), "Thanks. Contact the owner next.")}
        />
      </section>

      <section className="hcr2-verify-section">
        <h4>2. Contact {config?.discord.owner_handles.join(", ") || "the site owner"}</h4>
        <p>Send one of them a direct message containing:</p>
        <ul className="hcr2-method-list">
          <li>
            Your hcr2.xyz community username: <strong>{communityUsername ?? "(not set)"}</strong>
          </li>
          <li>
            The HCR2 player name you selected:{" "}
            <strong>{liveRequest?.player_name ?? selected?.name_player ?? "(not selected)"}</strong>
          </li>
          <li>That you want to complete screen-share verification.</li>
        </ul>
        <ClaimButton
          label="I've contacted the owner"
          doneLabel="Contacted the owner"
          claimed={Boolean(liveRequest?.contacted_owner_claimed)}
          busy={busy}
          onClaim={() =>
            claim(() => confirmHcr2ContactedOwner(), "Thanks. Arrange the screen-share next.")
          }
        />
      </section>

      <section className="hcr2-verify-section">
        <h4>3. Arrange the screen-share</h4>
        <p className="hcr2-discord-explainer">
          At the agreed time, join a voice call with the owner and share your screen showing
          your HCR2 account and the player name you&apos;re linking. You don&apos;t need a
          microphone and you don&apos;t need to speak. Just share your screen so staff can
          check that you control the account.
        </p>
        <p className="frontend-muted">
          Appointment status: {liveRequest?.appointment_status ?? "waiting_contact"}
        </p>
        <p className="form-hint">
          You do not need to leave your current HCR2 team for this method.
        </p>
        <ClaimButton
          label="The screen-share is arranged"
          doneLabel="Screen-share arranged"
          claimed={liveRequest?.step === "discord_schedule"}
          busy={busy}
          onClaim={() => claim(() => confirmHcr2DiscordReady(), "Ready to submit your request.")}
        />
      </section>
    </div>
  );

  const challengeVerifyBody = (
    <div className="hcr2-step-body">
      <section className="hcr2-team-details">
        <h4>1. Your assigned distance</h4>
        {challengeDistance ? (
          <>
            <div className="hcr2-detail-row">
              <span className="hcr2-detail-label">Distance</span>
              <strong>{challengeDistance} m</strong>
              <CopyValueButton value={`${challengeDistance} m`} label="Copy" />
            </div>
            <p className="frontend-muted">
              This distance was picked for you and cannot be changed or re-rolled. Drive it with a
              jeep in Countryside Adventure.
            </p>
          </>
        ) : (
          <p className="frontend-muted">
            No distance has been assigned yet. Go back and choose the jeep challenge method again.
          </p>
        )}
        {config?.challenge.instructions && (
          <p className="frontend-muted">{config.challenge.instructions}</p>
        )}
      </section>

      <section className="hcr2-verify-section">
        <h4>2. Send your challenge link</h4>
        <p>
          Make challenge about run and paste the link to it here. It has to
          start with <code>{challengePrefix}</code>
        </p>
        <label className="hcr2-challenge-field">
          Challenge link
          <input
            type="url"
            inputMode="url"
            value={challengeUrl}
            placeholder={`${challengePrefix}your-challenge-id`}
            maxLength={512}
            disabled={busy}
            onChange={(event) => setChallengeUrl(event.target.value)}
          />
        </label>
        <ClaimButton
          label="I've sent my challenge link"
          doneLabel="Challenge link sent"
          claimed={Boolean(liveRequest?.challenge_link_claimed)}
          busy={busy}
          blockedHint={!challengeUrl.trim() ? "Paste your challenge link above first." : undefined}
          onClaim={() =>
            claim(
              () => submitHcr2ChallengeLink(challengeUrl.trim()),
              "Thanks. Continue to submit your request."
            )
          }
        />
        {liveRequest?.challenge_link_claimed && liveRequest?.challenge_url && (
          <p className="form-hint">
            <a href={liveRequest.challenge_url} target="_blank" rel="noreferrer noopener">
              {liveRequest.challenge_url}
            </a>
          </p>
        )}
        <p className="form-hint">
          An administrator opens the challenge and checks your driver profile.
          Sending a link does not link your name on its own.
        </p>
      </section>
    </div>
  );

  const verifyBodies: Record<Hcr2LinkMethod, ReactElement> = {
    team: teamVerifyBody,
    discord_screen_share: discordVerifyBody,
    playhcr_challenge: challengeVerifyBody
  };

  const verifyStep: WizardStep = {
    id: "verify",
    title: method ? VERIFY_STEP_TITLES[method] : "Verify your HCR2 account",
    body: method ? verifyBodies[method] : null
  };

  const summaryStep: WizardStep = {
    id: "summary",
    title: "Review and submit",
    body: (
      <div className="hcr2-step-body">
        <dl className="hcr2-summary">
          <div>
            <dt>Selected HCR2 player name</dt>
            <dd>{liveRequest?.player_name ?? selected?.name_player ?? "(not selected)"}</dd>
          </div>
          <div>
            <dt>Verification method</dt>
            <dd>{method ? METHOD_LABELS[method] : "(not selected)"}</dd>
          </div>
          <div>
            <dt>Your hcr2.xyz username</dt>
            <dd>{communityUsername ?? "(not set)"}</dd>
          </div>
          <div>
            <dt>Discord account on file</dt>
            <dd>{discordUsername ?? "(not shared)"}</dd>
          </div>
          <div>
            <dt>Current status</dt>
            <dd>{STATUS_LABELS[liveRequest?.status ?? "draft"]}</dd>
          </div>
          {liveRequest?.verification_method === "team" && (
            <div>
              <dt>Verification code</dt>
              <dd>
                <code>{liveRequest?.code ?? "(generate one first)"}</code>
              </dd>
            </div>
          )}
          {liveRequest?.verification_method === "playhcr_challenge" && (
            <>
              <div>
                <dt>Assigned distance</dt>
                <dd>{challengeDistance ? `${challengeDistance} m` : "(not assigned)"}</dd>
              </div>
              <div>
                <dt>Challenge link</dt>
                <dd>
                  {liveRequest?.challenge_url ? (
                    <a
                      href={liveRequest.challenge_url}
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      {liveRequest.challenge_url}
                    </a>
                  ) : (
                    "(not sent yet)"
                  )}
                </dd>
              </div>
            </>
          )}
        </dl>

        <p className="hcr2-warn">
          Submitting sends your request to the administrators. Nothing is verified automatically,
          and your name is not linked until an administrator reviews it.
        </p>

        <label className="hcr2-inline-check">
          <input
            type="checkbox"
            checked={instructionsFollowed}
            onChange={(event) => setInstructionsFollowed(event.target.checked)}
          />
          I have followed the instructions above and want to submit my request
        </label>

        <p className="form-hint">
          We never ask for your password, recovery codes, or unrelated personal information. Calls
          are not recorded and screenshots are not retained.
        </p>
      </div>
    )
  };

  const steps = [selectStep, methodStep, verifyStep, summaryStep];

  function canContinue(): boolean {
    if (stepIndex === 0) {
      return Boolean(selected) && nameConfirmed;
    }
    if (stepIndex === 1) {
      return liveRequest?.step !== "choose_method";
    }
    if (stepIndex === 2) {
      return methodComplete;
    }
    return instructionsFollowed;
  }

  async function handleContinue() {
    setError("");
    setNotice("");
    try {
      if (stepIndex === 0) {
        if (!selected) return;
        await action.mutateAsync(() => startHcr2LinkRequest(selected.name_player));
        setNotice("Player name selected. Choose a verification method next.");
        setStepOverride(1);
      } else if (stepIndex === 1) {
        setStepOverride(2);
      } else if (stepIndex === 2) {
        setStepOverride(3);
      } else {
        await action.mutateAsync(() => submitHcr2LinkRequest(true, methodComplete));
        setNotice("Submitted — awaiting admin review.");
        setInstructionsFollowed(false);
      }
    } catch (continueError) {
      setError(continueError instanceof Error ? continueError.message : "Could not continue.");
    }
  }

  // ---------------------------------------------------------------- render

  if (statusQuery.isLoading) {
    return (
      <div className="account-card">
        <h1>Linked HCR2 Account</h1>
        <p className="community-status">Loading your linking status...</p>
      </div>
    );
  }

  if (statusQuery.isError) {
    return (
      <div className="account-card">
        <h1>Linked HCR2 Account</h1>
        <p className="frontend-error">Could not load your linking status. Please try again.</p>
      </div>
    );
  }

  const submitted = liveRequest?.status === "submitted";
  const decided =
    !liveRequest && request !== null && request.status !== "draft" && request.status !== "in_progress";

  return (
    <div className="account-card hcr2-link-card">
      <h1>
        Linked HCR2 Account
        <BetaBadge feature="hcr2_account_linking" />
      </h1>

      {link && (
        <div className="hcr2-link-current">
          <p className="hcr2-link-current-name">
            <span className="status-pill status-pill--verified">Verified</span>
            <strong>{link.player_name}</strong>
          </p>
          <p className="frontend-muted">
            Verified {link.approved_at ? formatMemberSince(link.approved_at) : "recently"}. Records
            matching this player name are shown on your profile; this does not claim ownership of
            records set before verification.
          </p>
          <button
            className="button-ghost"
            type="button"
            disabled={busy}
            onClick={() => {
              if (!window.confirm("Unlink this HCR2 player name from your profile?")) return;
              setError("");
              action.mutate(unlinkHcr2Player);
            }}
          >
            Unlink
          </button>
        </div>
      )}

      {submitted && (
        <p className="hcr2-status-banner is-submitted">
          <strong>Submitted! awaiting admin review.</strong> An administrator will check your
          verification and decide. Nothing has been verified automatically.
        </p>
      )}

      {request?.status === "rejected" && (
        <p className="hcr2-status-banner is-rejected">
          <strong>This request was not approved.</strong>{" "}
          {request.rejection_category
            ? (REJECTION_LABELS[request.rejection_category] ?? "please contact staff")
            : "Please contact staff."}
        </p>
      )}

      {request?.status === "expired" && (
        <p className="hcr2-status-banner is-expired">
          <strong>This request expired.</strong> You can start a new one below.
        </p>
      )}

      {!link && !submitted && (
        <>
          {!liveRequest && (
            <p className="frontend-muted">
              Link an HCR2 player name to your community profile. Verification is always checked
              manually by an administrator, because we have no official way to verify an in-game
              account automatically.
            </p>
          )}

          {decided && !restarting ? (
            <button className="button" type="button" disabled={busy} onClick={beginFreshRequest}>
              Start a new request
            </button>
          ) : (
            <Hcr2LinkWizard
              steps={steps}
              currentIndex={Math.min(stepIndex, steps.length - 1)}
              onBack={() => {
                setError("");
                setNotice("");
                const clamped = Math.min(stepIndex, steps.length - 1);
                if (clamped === 0) {
                  setSelected(null);
                  setNameConfirmed(false);
                  return;
                }
                setStepOverride(clamped - 1);
              }}
              backDisabled={stepIndex === 0 && !selected}
              onContinue={handleContinue}
              continueLabel={stepIndex === 3 ? "Submit for review" : "Continue"}
              continueDisabled={!canContinue()}
              busy={busy}
              error={error}
              notice={notice}
            />
          )}
        </>
      )}

      {liveRequest && !submitted && (
        <button
          className="button-ghost hcr2-cancel-request"
          type="button"
          disabled={busy}
          onClick={() => {
            if (!window.confirm("Cancel this request? You can start a new one later.")) return;
            setError("");
            action.mutate(async () => {
              await cancelHcr2LinkRequest();
              beginFreshRequest();
            });
          }}
        >
          Cancel this request
        </button>
      )}
    </div>
  );
}