CREATE SEQUENCE badge_category_id_seq;
CREATE TABLE badge_category (
    id integer PRIMARY KEY DEFAULT nextval('badge_category_id_seq'),
    identifier text NOT NULL,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    sort_order integer NOT NULL DEFAULT 0,
    enabled boolean NOT NULL DEFAULT TRUE,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT badge_category_identifier_key UNIQUE (identifier),
    CONSTRAINT badge_category_identifier_check CHECK (identifier ~ '^[a-z0-9][a-z0-9_-]*$')
);
ALTER SEQUENCE badge_category_id_seq OWNED BY badge_category.id;
CREATE INDEX badge_category_enabled_order_idx ON badge_category (enabled, sort_order, id);

CREATE SEQUENCE badge_id_seq;
CREATE TABLE badge (
    id integer PRIMARY KEY DEFAULT nextval('badge_id_seq'),
    identifier text NOT NULL,
    category_id integer NOT NULL REFERENCES badge_category (id) ON DELETE RESTRICT,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    icon_path text NOT NULL DEFAULT '',
    badge_type text NOT NULL,
    award_method text NOT NULL DEFAULT 'manual',
    rarity text NOT NULL DEFAULT 'common',
    requirement_type text,
    requirement_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    enabled boolean NOT NULL DEFAULT TRUE,
    hidden_until_unlocked boolean NOT NULL DEFAULT FALSE,
    revocable boolean NOT NULL DEFAULT TRUE,
    featureable boolean NOT NULL DEFAULT TRUE,
    permanent boolean NOT NULL DEFAULT TRUE,
    archived_at timestamp without time zone,
    expires_at timestamp without time zone,
    discord_role_id text,
    discord_sync_enabled boolean NOT NULL DEFAULT FALSE,
    sort_order integer NOT NULL DEFAULT 0,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT badge_identifier_key UNIQUE (identifier),
    CONSTRAINT badge_identifier_check CHECK (identifier ~ '^[a-z0-9][a-z0-9_-]*$'),
    CONSTRAINT badge_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT badge_icon_path_check CHECK (icon_path = '' OR icon_path LIKE '/img/%')
);
ALTER SEQUENCE badge_id_seq OWNED BY badge.id;
CREATE INDEX badge_category_enabled_idx ON badge (category_id, enabled, archived_at, sort_order);
CREATE INDEX badge_type_enabled_idx ON badge (badge_type, enabled, archived_at);
CREATE INDEX badge_requirement_type_idx ON badge (requirement_type) WHERE requirement_type IS NOT NULL;

CREATE SEQUENCE community_user_badge_id_seq;
CREATE TABLE community_user_badge (
    id integer PRIMARY KEY DEFAULT nextval('community_user_badge_id_seq'),
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    badge_id integer NOT NULL REFERENCES badge (id) ON DELETE RESTRICT,
    active boolean NOT NULL DEFAULT TRUE,
    source text NOT NULL DEFAULT 'manual',
    awarded_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    awarded_by text,
    reason text,
    public_reason text,
    expires_at timestamp without time zone,
    revoked_at timestamp without time zone,
    revoked_by text,
    revocation_reason text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT community_user_badge_user_badge_key UNIQUE (community_user_id, badge_id),
    CONSTRAINT community_user_badge_source_check CHECK (source IN ('automatic', 'manual')),
    CONSTRAINT community_user_badge_revoked_consistency CHECK (
        (active = TRUE AND revoked_at IS NULL AND revoked_by IS NULL AND revocation_reason IS NULL)
        OR active = FALSE
    )
);
ALTER SEQUENCE community_user_badge_id_seq OWNED BY community_user_badge.id;
CREATE INDEX community_user_badge_active_idx
    ON community_user_badge (community_user_id, active, awarded_at DESC);
CREATE INDEX community_user_badge_badge_idx ON community_user_badge (badge_id);

CREATE SEQUENCE badge_award_history_id_seq;
CREATE TABLE badge_award_history (
    id integer PRIMARY KEY DEFAULT nextval('badge_award_history_id_seq'),
    user_badge_id integer NOT NULL REFERENCES community_user_badge (id) ON DELETE CASCADE,
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    badge_id integer NOT NULL REFERENCES badge (id) ON DELETE RESTRICT,
    action text NOT NULL,
    actor text,
    reason text,
    event_key text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT badge_award_history_action_check CHECK (action IN ('awarded', 'revoked'))
);
ALTER SEQUENCE badge_award_history_id_seq OWNED BY badge_award_history.id;
CREATE INDEX badge_award_history_user_idx
    ON badge_award_history (community_user_id, created_at DESC, id DESC);
CREATE INDEX badge_award_history_badge_idx ON badge_award_history (badge_id, created_at DESC);
CREATE UNIQUE INDEX badge_award_history_event_key_idx
    ON badge_award_history (event_key, badge_id, action) WHERE event_key IS NOT NULL;

CREATE TABLE badge_progress (
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    badge_id integer NOT NULL REFERENCES badge (id) ON DELETE CASCADE,
    progress_value integer NOT NULL DEFAULT 0,
    target_value integer NOT NULL DEFAULT 1,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT badge_progress_pk PRIMARY KEY (community_user_id, badge_id),
    CONSTRAINT badge_progress_values_check CHECK (progress_value >= 0 AND target_value > 0)
);

CREATE SEQUENCE featured_badge_id_seq;
CREATE TABLE featured_badge (
    id integer PRIMARY KEY DEFAULT nextval('featured_badge_id_seq'),
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    user_badge_id integer NOT NULL REFERENCES community_user_badge (id) ON DELETE CASCADE,
    badge_id integer NOT NULL REFERENCES badge (id) ON DELETE CASCADE,
    position integer NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT featured_badge_user_badge_key UNIQUE (user_badge_id),
    CONSTRAINT featured_badge_user_position_key UNIQUE (community_user_id, position),
    CONSTRAINT featured_badge_position_check CHECK (position BETWEEN 1 AND 5)
);
ALTER SEQUENCE featured_badge_id_seq OWNED BY featured_badge.id;
CREATE INDEX featured_badge_user_idx ON featured_badge (community_user_id, position);

CREATE TABLE community_progression (
    community_user_id integer PRIMARY KEY REFERENCES community_user (id) ON DELETE CASCADE,
    total_xp integer NOT NULL DEFAULT 0,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT community_progression_total_xp_check CHECK (total_xp >= 0)
);

CREATE SEQUENCE xp_transaction_id_seq;
CREATE TABLE xp_transaction (
    id integer PRIMARY KEY DEFAULT nextval('xp_transaction_id_seq'),
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    amount integer NOT NULL,
    event_type text NOT NULL,
    event_key text,
    reason text NOT NULL DEFAULT '',
    actor text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT xp_transaction_amount_check CHECK (amount <> 0)
);
ALTER SEQUENCE xp_transaction_id_seq OWNED BY xp_transaction.id;
CREATE INDEX xp_transaction_user_idx ON xp_transaction (community_user_id, created_at DESC, id DESC);
CREATE UNIQUE INDEX xp_transaction_event_key_idx
    ON xp_transaction (community_user_id, event_key) WHERE event_key IS NOT NULL;

CREATE TABLE progression_event (
    event_key text PRIMARY KEY,
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    event_type text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'processed',
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp without time zone,
    CONSTRAINT progression_event_status_check CHECK (status IN ('processed', 'ignored', 'failed'))
);
CREATE INDEX progression_event_user_idx ON progression_event (community_user_id, created_at DESC);

CREATE TABLE progression_evaluation (
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    requirement_type text NOT NULL,
    evaluated_on date NOT NULL DEFAULT CURRENT_DATE,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT progression_evaluation_pk PRIMARY KEY (community_user_id, requirement_type, evaluated_on)
);

ALTER TABLE community_user ADD COLUMN show_badges boolean NOT NULL DEFAULT TRUE;
ALTER TABLE community_user ADD COLUMN show_xp boolean NOT NULL DEFAULT FALSE;
