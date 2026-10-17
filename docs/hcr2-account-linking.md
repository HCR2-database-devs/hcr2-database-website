# Phase 4 — HCR2 Player Account Linking

This document covers the fourth phase of the hcr2.xyz community system: letting
a member link an HCR2 Adventure player name to their community profile through a
guided, manually-reviewed verification wizard.

## The one thing to understand first

**We have no official Fingersoft API.** Nothing in this system can read HCR2
in-game chat, confirm team membership, or verify that an account exists. Every
request therefore ends with a human reading evidence and an administrator making
a decision.

Concretely, this means:

- No code path in the backend can approve a request. `submit_request` only ever
  writes `submitted`.
- The buttons labelled "I've joined the team" and "I've sent the code" record the
  user's **statement**. They are stored with `*_confirmed_at` timestamps and are
  labelled as claims in the admin panel.

Because those buttons prove nothing, the UI treats them as self-declarations
rather than as actions with an outcome. Each one:

- stays disabled until its prerequisite is met (for example "I've sent the
  code" needs the visibility tick box first) and shows the reason,
- switches to a **✓ Done** state once recorded, so a click always has a visible
  effect,
- never implies the step was verified.

`GET /community/hcr2-link/status` also separates the two kinds of request via
`request_is_live`. Only a `draft`, `in_progress` or `submitted` request is
resumable; an approved, rejected, expired or cancelled one is returned for
display with `request_is_live: false`. Without that distinction a finished
request — for instance the approved attempt left behind after an admin revokes
a link — looks resumable, and the wizard dead-ends instead of offering a fresh
start.
- The site never says a user "has been verified" until an administrator says so.
- Nothing about this is exposed through the API-key bot endpoint beyond the
  approved player name and its approval date.

The dropdown establishes only that a name exists in the records database. It does
**not** establish that the user owns the HCR2 account behind it.

## The three verification methods

### Method A — Verification team

1. The user leaves their current team. They cannot be in two teams at once.
2. They join the designated verification team using the configured team name and
   team password.
3. The site generates a code containing their exact selected player name and a
   random token, for example `PlayerName:K7M4-X9Q2`.
4. They paste the complete code into that team's in-game chat.
5. They confirm they sent it, and submit the request.
6. An administrator reads the team chat, finds the code, and compares it against
   the code shown in the review queue.

**This method does not work with the Chinese version of HCR2.** The wizard says
so before the user commits, and repeats it in the step itself.

**Censorship.** HCR2's in-game automoderation sometimes replaces parts of a
player name or a code with `*`. The wizard tells the user, prominently, to reroll
the code if anything is censored, and the backend refuses to accept a
"code sent" confirmation for a code or player name containing `*`. Reroll is
limited to once every 10 seconds, enforced server-side.

### Method B — Discord screen-share

1. The user joins the Discord server using the configured invite.
2. They DM one of the configured owner handles to arrange a time.
3. At the agreed time they join a voice call and **share their screen** showing
   their HCR2 account and the player name they are linking.
4. **No microphone is required and they do not need to speak.** Screen-sharing
   is sufficient.
5. An administrator records the appointment status and approves or rejects.

This method does **not** require the user to leave their current HCR2 team.

Nothing about Discord DMs or screen sharing is automated.

### Method C — playhcr.com jeep challenge

1. Choosing the method makes the **server** draw a random distance between 1 and
   `HCR2_LINK_CHALLENGE_MAX_DISTANCE_M` metres (2000 by default).
2. The user drives that distance with a jeep in Countryside Adventure.
3. They turn the run into a challenge on playhcr.com and send the link to it.
   The link must start with `https://playhcr.com/challenge?id=` followed by a
   non-empty challenge id; anything else is rejected by the backend, not just by
   the browser.
4. An administrator opens the challenge and compares its distance with the
   assigned one before approving.

**The distance cannot be chosen and cannot be re-rolled.** It is drawn with
`secrets` on the server when the method is picked, stored on the request, and
kept if the member goes back and picks the method again — otherwise a member
could keep re-rolling until a 1 m attempt came up. A member who finds the
distance impossible cancels the request and starts a new one.

This method does **not** require leaving the current HCR2 team, and works with
every version of HCR2 that can create a challenge.

Sending the link proves nothing on its own: the site cannot open playhcr.com or
compare the challenge, so an administrator always makes the decision.

## Configuration

All of this lives in the environment. Nothing is hardcoded in the frontend.

```
# Feature flag. Ships as BETA; see docs/beta-testing.md.
FEATURE_HCR2_ACCOUNT_LINKING=BETA

# Method A. Both ship empty so nothing is invented before an operator fills
# them in. While the team name is empty the method card reads "Not configured
# yet" and selecting it returns 503.
HCR2_LINK_VERIFICATION_TEAM_NAME=
HCR2_LINK_VERIFICATION_TEAM_PASSWORD=
HCR2_LINK_VERIFICATION_TEAM_DETAILS=

# Method B.
HCR2_LINK_DISCORD_INVITE_URL=https://discord.gg/GGQPunUbHj
HCR2_LINK_OWNER_HANDLES=nipatsuyt,titaniumhcr2,yazi.arod

# Method C. Ships disabled: the card reads "Not configured yet" and selecting
# it returns 503 until an operator enables it.
HCR2_LINK_CHALLENGE_ENABLED=false
HCR2_LINK_CHALLENGE_INSTRUCTIONS=
HCR2_LINK_CHALLENGE_MAX_DISTANCE_M=2000

# Code behaviour.
HCR2_LINK_CODE_TTL_SECONDS=900
HCR2_LINK_CODE_REROLL_COOLDOWN_SECONDS=10

# Request lifetime and abuse limits.
HCR2_LINK_REQUEST_TTL_DAYS=30
HCR2_LINK_CODE_RATE_LIMIT=6
HCR2_LINK_CODE_RATE_WINDOW_SECONDS=300
HCR2_LINK_REQUEST_RATE_LIMIT=5
HCR2_LINK_REQUEST_RATE_WINDOW_SECONDS=3600
HCR2_LINK_MAX_OPEN_REQUESTS=3

# Admin action limit.
HCR2_LINK_ADMIN_ACTION_RATE_LIMIT=60
HCR2_LINK_ADMIN_ACTION_RATE_WINDOW_SECONDS=3600
```

### About the team password

`HCR2_LINK_VERIFICATION_TEAM_PASSWORD` is the in-game password for the
verification team. It is read only from the environment and returned only by
`GET /api/v1/community/hcr2-link/config`, which already requires a Discord login
and the feature flag. It is:

- never written to the database,
- never written to the activity log,
- never included in an admin review payload,
- never included in a notification.

Anyone who can open the wizard can read it. That is inherent to HCR2 team
joining — the code has to be shareable for people to join the team at all — so
beta access effectively grants team-entry access. **Rotating it is a one-line
`.env` change and a backend restart**, with no deploy and no code change.

### About the challenge link prefix

`https://playhcr.com/challenge?id=` is a constant in
`backend/app/core/hcr2_challenge.py`, not an environment variable: loosening the
accepted link shape must not be a config change. `GET .../config` returns the same
prefix so the wizard can label the input, and the service validates against it
again on the way in.

### About the code hashing secret

Verification code tokens are hashed with HMAC-SHA256 before storage, using
`AUTH_SHARED_SECRET`. No new secret variable was introduced. If it is empty the
code still works using an unkeyed SHA-256 digest, which keeps local development
simple; production should always set one.

## Migrations

Migration `20261016_add_hcr2_account_linking` adds:

| Object | Purpose |
| --- | --- |
| `hcr2_account_link` | Active and historical links, one active per player name and per account |
| `hcr2_verification_request` | Wizard state, user claims, code metadata, admin decision |
| `hcr2_verification_request_step` | Per-request audit history |
| `community_action_rate_limit` | Fixed-window counters for the rate limits above |
| `idx_player_name_lower_prefix` | Index that makes the dropdown's prefix search index-backed |
| `community_user.show_hcr2_player_name` | Per-member visibility toggle for the linked name |

Migration `20261017_add_hcr2_challenge_verification` then adds method C: the
`challenge_distance_m`, `challenge_url`, `challenge_id` and
`challenge_confirmed_at` columns on `hcr2_verification_request`, the two new
method values and the `challenge_assign` / `challenge_link` steps in the CHECK
constraints, and the `challenge_mismatch` rejection category. The distance is
constrained to 1-2000 m and the stored URL is constrained to the accepted
prefix, so even a direct database write cannot store a lookalike link.

Apply them with the tracked runner, which skips anything already applied:

```bash
python3 scripts/migrate.py status
python3 scripts/migrate.py up --dry-run
python3 scripts/migrate.py up
```

**Deploy order matters.** `PROFILE_COLUMNS` in
`backend/app/repositories/community_user.py` now contains two sub-selects
against `hcr2_account_link`, which every community profile read depends on. Apply
the migration **before** restarting the backend, or profile endpoints will fail
with a database error until it is applied.

The code token is stored twice in `hcr2_verification_request`:

- `code_token_hash` — the keyed hash, used for any server-side comparison and
  never selected by the admin query or returned by any endpoint.
- `code_value` — the plaintext an administrator has to read in order to compare
  it against what they see in team chat. It is admin-only and authorises nothing:
  approval always requires a human decision.

## Admin review process

Admin panel: **Community → HCR2 account links**.

### Review queue

The default filter is `Submitted (awaiting review)`. Each card shows the player
name, request id, community username, method, status and creation time.
**Review** expands the full payload:

- hcr2.xyz community username and account id
- Discord display name **and Discord user ID**, for reliable identification
  inside the admin panel only
- the exact selected player name and its normalized form
- the wizard step and whether the request has actually been submitted
- for team verification: the exact generated code with a copy button, and
  separately whether the user claims to have joined the team and sent the code
- for Discord verification: whether the user claims to have joined the server and
  contacted the owner, plus the appointment status and time
- for challenge verification: the assigned distance, the submitted
  playhcr.com challenge link as a clickable URL, and its challenge id — compare
  the distance in the challenge against the assigned one
- attempt count, whether it is a resubmission, and what it supersedes
- per-step history with timestamps
- previous and competing attempts by this account or anyone else claiming the
  same player name
- a conflict warning when more than one account claims the same name
- a private admin note field, never shown to the member

### Actions

| Action | Effect |
| --- | --- |
| Approve and link | Creates the active link in a transaction |
| Ask to retry | Reopens the request for another attempt, no decision |
| Reject | Requires a reason category and a reason shown to the member |
| Screen-share appointment | Sets the appointment status and time (Discord method only) |
| Cancel / Expire | Moves the request to a terminal status |
| Revoke / Suspend / Restore | Changes an existing link's status, reason required |

Approval runs in a database transaction that locks the request row with
`FOR UPDATE`, so two admins cannot both create a link for the same request, and
revalidates the player name against the records database a third time. The
partial unique indexes `uq_hcr2_account_link_active_player` and
`uq_hcr2_account_link_active_user` are the final backstop; a violation is
translated into the same generic message the user sees, which never names the
conflicting account.

Every decision is written to `activity_log` with `entity_type` of
`hcr2_verification_request` or `hcr2_account_link`, and the member receives a
community notification.

### Verification procedure, method A

1. Open the request and copy the code.
2. Join the verification team in game and read its chat.
3. Look for the exact player name and code, with no `*` substitutions.
4. Approve only if both are present and uncensored. If not, reject with
   `code_not_visible`.

**Never approve because the code looks right.** The site's buttons prove
nothing; only the chat does.

### Verification procedure, method B

1. Confirm the member DM'd you and agree a time.
2. Set the appointment status and time.
3. At the agreed time, take the screen-share and check the HCR2 account name
   against the selected player name.
4. Approve or reject.

## Player names and record ownership

The dropdown is populated exclusively from `player` rows joined to
`world_record`. Because superseded records are retained with `current = 0`, a
single `EXISTS` covers players who still hold a world record **and** players
whose records are only historical.

The name is revalidated on the backend when the request starts, when it is
submitted, and again when it is approved. Posting an arbitrary name straight to
the API fails exactly as it would in the UI.

If a name is already actively linked to another account, the user sees:

> This player name is already linked to another community account. Please
> contact staff if you believe this is a mistake.

No information about the other account is revealed.

**Linking does not transfer record ownership.** The profile shows "Records
matching this player name" and explicitly does not claim that every historical
record under that name belongs to the linked member. Historical records are never
rewritten or reassigned.

Note that `player.name_player` is unique **case-sensitively**, so `Bob` and `bob`
are two distinct rows. Links are keyed on a case-folded, whitespace-collapsed
form so both spellings cannot be active at once.

## Beta access

`FEATURE_HCR2_ACCOUNT_LINKING` defaults to `BETA`, which restricts the feature to
`BETA_DISCORD_IDS` plus admins. Enforcement is server-side on every Phase 4
endpoint; a direct API call from a non-tester gets `403` with `"This feature is
currently disabled"`. Admins bypass the gate so they can always review the queue.
See `docs/beta-testing.md`.

## Security summary

- Identity comes only from the verified `WC_TOKEN` cookie. No endpoint accepts a
  Discord id, an admin flag or a community user id from the client.
- Admin endpoints reuse the existing `ALLOWED_DISCORD_IDS` check. The acting
  administrator always comes from the cookie, never from a request body.
- Codes use `secrets.choice` over a Crockford-style base32 alphabet that omits
  `I`, `O`, `0` and `1` so a mistyped code cannot become a different valid token.
  Codes are never derived from usernames, Discord ids, timestamps or sequence ids.
- The delimiter `:` cannot appear in a token, and codes are split from the right,
  so a player name containing spaces, `:` or other punctuation is unambiguous.
- The reroll cooldown is enforced by the `UPDATE`'s `WHERE` clause, so a client
  that ignores the countdown still cannot obtain a second code, and rerolling
  invalidates the previous code in the same statement.
- Rate-limit keys are HMACed, so the rate-limit table never contains Discord ids
  or IP addresses in the clear.
- `code_token_hash`, `admin_note`, `decided_by_admin`, `rejection_reason` and all
  Discord identifiers are stripped from every user-facing response.
- Linking is never required to use any other community feature.

## Known limitations

- **The dropdown does not prove ownership.** It proves a name holds a world
  record.
- **The team-chat method depends on an administrator actually reading team
  chat.** If nobody does, requests sit in the queue.
- **The team method does not work with the Chinese version of HCR2**, because
  those servers are separate from the verification team.
- **The team password is readable by anyone who can open the wizard.**
- **A player whose record rows were deleted outright** is no longer eligible,
  because the database no longer retains evidence that they ever held a world
  record. Names with superseded (`current = 0`) history are still eligible.
- **Search uses substring matching.** The added index accelerates prefix lookups,
  but `ILIKE '%term%'` still scans. That is fine at current scale; `pg_trgm`
  would be the upgrade path if the player table grows substantially. `pg_trgm` is
  deliberately not enabled because it requires an extension privilege the
  application database role may not have.
- **Discord DMs and screen sharing are manual**, and calls are not recorded and
  screenshots are not retained.
- **The site cannot open a playhcr.com challenge.** A stored method-C link is a
  member's claim; an administrator has to open it and compare the distance
  manually, and a wrong comparison approves someone else's account.
- **A 2000 m attempt may be practically impossible** for some players. There is
  deliberately no re-roll, so such a member has to cancel and start again.
- We never ask for a password, recovery code, or unrelated personal information.