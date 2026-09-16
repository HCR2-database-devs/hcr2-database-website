# Beta Testing System

This document explains how the beta tester / feature flag system works for
hcr2.xyz. It is designed so that **only explicitly marked** features are ever
gated. Normal site updates (records, bug fixes, existing admin functionality)
are never treated as beta automatically.

Current Phase 1/2 community features all start out as `BETA`:

| Feature            | Flag                          | Default |
| ------------------ | ----------------------------- | ------- |
| Discord Accounts   | `FEATURE_DISCORD_ACCOUNTS`    | BETA    |
| Community Profiles | `FEATURE_COMMUNITY_PROFILES`  | BETA    |
| Profile Customization | `FEATURE_PROFILE_CUSTOMIZATION` | BETA |
| Community Members  | `FEATURE_COMMUNITY_MEMBERS`   | BETA    |
| Profile Reporting  | `FEATURE_PROFILE_REPORTING`   | BETA    |
| Community Notifications | `FEATURE_COMMUNITY_NOTIFICATIONS` | BETA |

## The three feature states

Every feature flag accepts one of these values:

- `DISABLED` — nobody can use the feature (frontend hides it, APIs return 403).
- `BETA` — only beta testers (and admins) can use the feature.
- `ENABLED` — everyone can use the feature.

Changing the value requires **no code changes** and **no frontend rebuild**:
the state is read from environment configuration on the backend and exposed to
the frontend through `GET /api/v1/auth/status`, so BETA badges appear and
disappear automatically.

## 1. Adding a Discord user to the beta tester list

Add the user's Discord ID to the `BETA_DISCORD_IDS` environment variable
(comma-separated), e.g.:

```
BETA_DISCORD_IDS=123456789012345678,987654321098765432
```

This is set in the backend environment (`.env`, deployment config, etc.). Users
are identified **only** by their Discord ID and the check happens **server-side**
— the allowlist is never sent to the frontend as usable gated content.

Admins (`ALLOWED_DISCORD_IDS`) automatically bypass beta restrictions, so they
do not need to be added to `BETA_DISCORD_IDS`.

## 2. Enabling / disabling a beta feature

To release a beta feature to everyone:

```
FEATURE_COMMUNITY_PROFILES=ENABLED
```

At that point every user gets access and the BETA badge disappears
automatically.

To temporarily disable a feature for everyone (including beta testers):

```
FEATURE_COMMUNITY_PROFILES=DISABLED
```

## 3. How to add a new beta feature in the future

New features are **not** beta by default. To gate a new feature you must
explicitly mark it:

1. Add an environment config field in `backend/app/core/config.py`, e.g.:
   ```python
   feature_some_new_thing: str = Field(default="BETA", validation_alias="FEATURE_SOME_NEW_THING")
   ```
   and include it in the `normalize_feature_flag` validator list.
2. Register the feature in `backend/app/core/features.py`:
   - add a constant to the `Feature` class, and
   - add a `"feature_some_new_thing"` entry to the `FEATURE_FIELDS` map.
3. Protect backend endpoints with the centralized gate, e.g. in the router:
   ```python
   _require_feature(request, auth_service, settings, Feature.SOME_NEW_THING)
   ```
   (see `backend/app/api/v1/community.py` for the existing pattern).
4. Gate the frontend:
   - add the feature name to the `FeatureName` union in `frontend/src/types/api.ts`,
   - wrap pages with `<FeatureGate feature="some_new_thing">`,
   - render `<BetaBadge feature="some_new_thing" />` next to relevant headings/labels.

Everything (beta membership, admin bypass, state lookup) lives in
`backend/app/core/features.py`, so moving tester/feature management into an
admin panel later will not require rewriting feature code.

## 4. Moving from BETA to ENABLED

Once Phase 2 is ready for public release:

```
FEATURE_COMMUNITY_PROFILES=ENABLED
```

..and anything else that is ready:

```
FEATURE_DISCORD_ACCOUNTS=ENABLED
FEATURE_PROFILE_CUSTOMIZATION=ENABLED
FEATURE_COMMUNITY_MEMBERS=ENABLED
FEATURE_PROFILE_REPORTING=ENABLED
FEATURE_COMMUNITY_NOTIFICATIONS=ENABLED
```

Everyone gets access, and the BETA badges disappear automatically because they
only render while a feature's state is `BETA`.

## Where things live

- Central feature logic: `backend/app/core/features.py` (`get_feature_state`,
  `is_beta_user`, `can_use_feature`).
- Configuration: `backend/app/core/config.py` (`BETA_DISCORD_IDS`, `FEATURE_*`).
- Auth payload for the frontend: `backend/app/api/v1/auth.py`
  (`beta` flag + global `features` map in `GET /api/v1/auth/status`).
- Frontend hooks: `frontend/src/lib/features.ts`.
- BETA badge: `frontend/src/components/BetaBadge.tsx`.
- Page gating / "feature unavailable" message:
  `frontend/src/components/FeatureGate.tsx`.

## Notes

- Logged-out users are never beta testers and cannot access `BETA` features.
- Everything is enforced on the backend, not just hidden in the UI. Direct API
  calls to community endpoints return `403` for non-beta users while a feature
  is in `BETA` or `DISABLED` state.