CREATE SEQUENCE community_user_id_seq;
CREATE TABLE community_user (
    id integer PRIMARY KEY DEFAULT nextval('community_user_id_seq'),
    discord_id text NOT NULL,
    discord_username text NOT NULL DEFAULT '',
    discord_avatar text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER SEQUENCE community_user_id_seq OWNED BY community_user.id;

CREATE UNIQUE INDEX idx_community_user_discord_id ON community_user (discord_id);
CREATE INDEX idx_community_user_created_at ON community_user (created_at);