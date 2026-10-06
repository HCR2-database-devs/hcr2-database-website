# Feature Flags and Beta Testing

This document explains the feature flag system for hcr2.xyz. It is designed so
that **only explicitly marked** features are ever gated. Normal site updates
(records, bug fixes, existing admin functionality) are never treated as beta
automatically.

The community features are **public**. All six flags default to `ENABLED`, so
they work out of the box for every signed-in user without any configuration:

| Feature                 | Flag                              | Default |
| ----------------------- | --------------------------------- | ------- |
| Discord Accounts        | `FEATURE_DISCORD_ACCOUNTS`        | ENABLED |
| Community Profiles      | `FEATURE_COMMUNITY_PROFILES`      | ENABLED |
| Profile Customization   | `FEATURE_PROFILE_CUSTOMIZATION`   | ENABLED |
| Community Members       | `FEATURE_COMMUNITY_MEMBERS`       | ENABLED |
| Profile Reporting       | `FEATURE_PROFILE_REPORTING`       | ENABLED |
| Community Notifications | `FEATURE_COMMUNITY_NOTIFICATIONS` | ENABLED |

Community features still require a Discord login — they are open to everyone,
not to anonymous visitors.

## The three feature states

Every feature flag accepts one of these values:

- `ENABLED` — everyone can use the feature. This is the default.
- `BETA` — only beta testers (and admins) can use the feature.
- `DISABLED` — nobody can use the feature (frontend hides it, APIs return 403).

Changing the value requires **no code changes** and **no frontend rebuild**:
the state is read from environment configuration on the backend and exposed to
the frontend through `GET /api/v1/auth/status`, so BETA badges appear and
disappear automatically.

An unset or unparseable flag fails closed: it is treated as `BETA`, so a typo in
the environment can never silently publish a feature that was meant to stay
restricted.

## 1. Temporarily disabling a feature

The main use of the flags now is the emergency kill switch. To take a feature
off the site without a deploy:

```
FEATURE_COMMUNITY_MEMBERS=DISABLED
```

The frontend hides the entry points and every related endpoint returns `403`
with `"This feature is currently disabled"`. Setting the value back to `ENABLED`
restores it.

## 2. Beta-testing a future feature

To preview an unreleased feature, set it to `BETA` and list the testers in
`BETA_DISCORD_IDS` (comma-separated Discord IDs):

```
FEATURE_SOME_NEW_THING=BETA
BETA_DISCORD_IDS=123456789012345678,987654321098765432
```

This is set in the backend environment (`.env`, deployment config, etc.). Users
are identified **only** by their Discord ID and the check happens **server-side**
— the allowlist is never sent to the frontend as usable gated content.

Admins (`ALLOWED_DISCORD_IDS`) automatically bypass beta restrictions, so they
do not need to be added to `BETA_DISCORD_IDS`. Logged-out users are never beta
testers and cannot access `BETA` features.

## 3. How to add a new flagged feature in future

New features are **not** gated automatically. To gate one you must explicitly
mark it:

1. Add an environment config field in `backend/app/core/config.py`, e.g.:
   ```python
   feature_some_new_thing: str = Field(default="DISABLED", validation_alias="FEATURE_SOME_NEW_THING")
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

Choose the default deliberately: `DISABLED` for something not ready at all,
`BETA` for something ready to preview, `ENABLED` for something ready to ship.

Everything (beta membership, admin bypass, state lookup) lives in
`backend/app/core/features.py`, so moving tester/feature management into an
admin panel later will not require rewriting feature code.

## Where things live

- Central feature logic: `backend/app/core/features.py` (`get_feature_state`,
  `is_beta_user`, `can_use_feature`).
- Configuration: `backend/app/core/config.py` (`BETA_DISCORD_IDS`, `FEATURE_*`).
- Auth payload for the frontend: `backend/app/api/v1/auth.py`
  (`beta` flag + global `features` map in `GET /api/v1/auth/status`).
- Frontend hooks: `frontend/src/lib/features.ts`.
- BETA badge: `frontend/src/components/BetaBadge.tsx`. It renders only while a
  feature's state is `BETA`, so it is invisible while everything is `ENABLED`.
- Page gating / "feature unavailable" message:
  `frontend/src/components/FeatureGate.tsx`.

## Notes

- Everything is enforced on the backend, not just hidden in the UI. Direct API
  calls to community endpoints return `403` while a feature is `BETA` or
  `DISABLED`, even if a caller bypasses the frontend.
- Production env templates must list the six `FEATURE_*` vars explicitly (see
  `DEPLOY.md`). An empty production environment otherwise relies on the code
  defaults, which currently happen to be `ENABLED`.