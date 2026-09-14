ALTER TABLE community_user
    ADD COLUMN username text,
    ADD COLUMN username_norm text,
    ADD COLUMN last_username_change_at timestamp without time zone,
    ADD COLUMN show_discord_username boolean NOT NULL DEFAULT FALSE,
    ADD COLUMN show_discord_avatar boolean NOT NULL DEFAULT FALSE;

CREATE UNIQUE INDEX idx_community_user_username_norm ON community_user (username_norm);

CREATE SEQUENCE community_username_history_id_seq;
CREATE TABLE community_username_history (
    id integer PRIMARY KEY DEFAULT nextval('community_username_history_id_seq'),
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    username text NOT NULL,
    username_norm text NOT NULL,
    changed_by_admin text NOT NULL DEFAULT '',
    changed_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER SEQUENCE community_username_history_id_seq OWNED BY community_username_history.id;

CREATE INDEX idx_community_username_history_user
    ON community_username_history (community_user_id, changed_at DESC);