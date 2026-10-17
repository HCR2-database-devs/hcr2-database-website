CREATE SEQUENCE hcr2_account_link_id_seq;

CREATE TABLE hcr2_account_link (
    id integer PRIMARY KEY DEFAULT nextval('hcr2_account_link_id_seq'),
    community_user_id integer NOT NULL,
    player_id integer NOT NULL,
    player_name text NOT NULL,
    player_name_norm text NOT NULL,
    verification_method text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    requested_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at timestamp without time zone,
    approved_by_admin text NOT NULL DEFAULT '',
    revoked_at timestamp without time zone,
    revoked_by_admin text NOT NULL DEFAULT '',
    revocation_reason text,
    CONSTRAINT hcr2_account_link_community_user_fk
        FOREIGN KEY (community_user_id)
        REFERENCES community_user (id)
        ON DELETE CASCADE,
    CONSTRAINT hcr2_account_link_player_fk
        FOREIGN KEY (player_id)
        REFERENCES player (id_player)
        ON DELETE RESTRICT,
    CONSTRAINT hcr2_account_link_method_check
        CHECK (verification_method IN ('team', 'discord_screen_share')),
    CONSTRAINT hcr2_account_link_status_check
        CHECK (status IN ('active', 'revoked', 'suspended'))
);

ALTER SEQUENCE hcr2_account_link_id_seq OWNED BY hcr2_account_link.id;

CREATE UNIQUE INDEX uq_hcr2_account_link_active_player
    ON hcr2_account_link (player_name_norm)
    WHERE status = 'active';

CREATE UNIQUE INDEX uq_hcr2_account_link_active_user
    ON hcr2_account_link (community_user_id)
    WHERE status = 'active';

CREATE INDEX idx_hcr2_account_link_user
    ON hcr2_account_link (community_user_id, requested_at DESC);

CREATE INDEX idx_hcr2_account_link_player_name_norm
    ON hcr2_account_link (player_name_norm);

CREATE INDEX idx_hcr2_account_link_status
    ON hcr2_account_link (status);

CREATE SEQUENCE hcr2_verification_request_id_seq;

CREATE TABLE hcr2_verification_request (
    id integer PRIMARY KEY DEFAULT nextval('hcr2_verification_request_id_seq'),
    community_user_id integer NOT NULL,
    link_id integer,
    player_id integer NOT NULL,
    player_name text NOT NULL,
    player_name_norm text NOT NULL,
    verification_method text NOT NULL DEFAULT 'team',
    status text NOT NULL DEFAULT 'draft',
    step text NOT NULL DEFAULT 'select_player',
    attempt_count integer NOT NULL DEFAULT 1,
    is_resubmission boolean NOT NULL DEFAULT FALSE,
    supersedes_request_id integer,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone NOT NULL,
    submitted_at timestamp without time zone,
    player_confirmed_at timestamp without time zone,
    team_joined_at timestamp without time zone,
    code_token_hash text,
    code_value text,
    code_generated_at timestamp without time zone,
    code_expires_at timestamp without time zone,
    code_last_generated_at timestamp without time zone,
    code_roll_count integer NOT NULL DEFAULT 0,
    code_sent_confirmed_at timestamp without time zone,
    code_visibility_confirmed boolean NOT NULL DEFAULT FALSE,
    discord_joined_at timestamp without time zone,
    contacted_owner_at timestamp without time zone,
    appointment_status text NOT NULL DEFAULT 'waiting_contact',
    appointment_at timestamp without time zone,
    appointment_note text,
    decided_at timestamp without time zone,
    decided_by_admin text NOT NULL DEFAULT '',
    rejection_category text,
    rejection_reason text,
    admin_note text,
    CONSTRAINT hcr2_verification_request_community_user_fk
        FOREIGN KEY (community_user_id)
        REFERENCES community_user (id)
        ON DELETE CASCADE,
    CONSTRAINT hcr2_verification_request_link_fk
        FOREIGN KEY (link_id)
        REFERENCES hcr2_account_link (id)
        ON DELETE SET NULL,
    CONSTRAINT hcr2_verification_request_player_fk
        FOREIGN KEY (player_id)
        REFERENCES player (id_player)
        ON DELETE RESTRICT,
    CONSTRAINT hcr2_verification_request_supersedes_fk
        FOREIGN KEY (supersedes_request_id)
        REFERENCES hcr2_verification_request (id)
        ON DELETE SET NULL,
    CONSTRAINT hcr2_verification_request_method_check
        CHECK (verification_method IN ('team', 'discord_screen_share')),
    CONSTRAINT hcr2_verification_request_status_check
        CHECK (status IN ('draft', 'in_progress', 'submitted', 'approved', 'rejected',
                          'expired', 'cancelled')),
    CONSTRAINT hcr2_verification_request_step_check
        CHECK (step IN ('select_player', 'choose_method', 'team_join', 'team_code',
                        'team_sent', 'discord_join', 'discord_contact',
                        'discord_schedule', 'summary')),
    CONSTRAINT hcr2_verification_request_attempt_positive
        CHECK (attempt_count > 0),
    CONSTRAINT hcr2_verification_request_appointment_status_check
        CHECK (appointment_status IN ('waiting_contact', 'awaiting_scheduling',
                                      'scheduled', 'awaiting_screen_share',
                                      'awaiting_decision', 'cancelled')),
    CONSTRAINT hcr2_verification_request_rejection_category_check
        CHECK (rejection_category IS NULL OR rejection_category IN (
            'code_not_visible', 'wrong_player_name', 'could_not_confirm_account',
            'screen_share_inconclusive', 'name_already_linked', 'no_contact',
            'request_cancelled', 'other'
        ))
);

ALTER SEQUENCE hcr2_verification_request_id_seq OWNED BY hcr2_verification_request.id;

CREATE INDEX idx_hcr2_verification_request_user
    ON hcr2_verification_request (community_user_id, created_at DESC);

CREATE INDEX idx_hcr2_verification_request_queue
    ON hcr2_verification_request (status, created_at)
    WHERE status = 'submitted';

CREATE INDEX idx_hcr2_verification_request_player_name_norm
    ON hcr2_verification_request (player_name_norm, created_at DESC);

CREATE INDEX idx_hcr2_verification_request_link
    ON hcr2_verification_request (link_id)
    WHERE link_id IS NOT NULL;

CREATE UNIQUE INDEX uq_hcr2_verification_request_open_code
    ON hcr2_verification_request (community_user_id)
    WHERE code_token_hash IS NOT NULL
      AND status IN ('draft', 'in_progress');

CREATE SEQUENCE hcr2_verification_request_step_id_seq;

CREATE TABLE hcr2_verification_request_step (
    id integer PRIMARY KEY DEFAULT nextval('hcr2_verification_request_step_id_seq'),
    request_id integer NOT NULL,
    step text NOT NULL,
    reached_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detail text NOT NULL DEFAULT '',
    CONSTRAINT hcr2_verification_request_step_request_fk
        FOREIGN KEY (request_id)
        REFERENCES hcr2_verification_request (id)
        ON DELETE CASCADE,
    CONSTRAINT hcr2_verification_request_step_step_check
        CHECK (step IN ('select_player', 'choose_method', 'team_join', 'team_code',
                        'team_sent', 'discord_join', 'discord_contact',
                        'discord_schedule', 'summary', 'submitted', 'approved',
                        'rejected', 'expired', 'cancelled', 'retry_requested'))
);

ALTER SEQUENCE hcr2_verification_request_step_id_seq
    OWNED BY hcr2_verification_request_step.id;

CREATE INDEX idx_hcr2_verification_request_step_request
    ON hcr2_verification_request_step (request_id, reached_at, id);

CREATE TABLE community_action_rate_limit (
    rate_key text PRIMARY KEY,
    request_count integer NOT NULL DEFAULT 1,
    window_started_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT community_action_rate_limit_count_positive CHECK (request_count > 0)
);

CREATE INDEX idx_community_action_rate_limit_window
    ON community_action_rate_limit (window_started_at);

CREATE INDEX idx_player_name_lower_prefix
    ON player (lower(name_player) text_pattern_ops);

ALTER TABLE community_user
    ADD COLUMN show_hcr2_player_name boolean NOT NULL DEFAULT TRUE;