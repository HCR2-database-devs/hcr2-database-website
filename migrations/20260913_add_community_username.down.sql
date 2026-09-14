DROP TABLE IF EXISTS community_username_history;
DROP SEQUENCE IF EXISTS community_username_history_id_seq;
DROP INDEX IF EXISTS idx_community_user_username_norm;

ALTER TABLE community_user
    DROP COLUMN IF EXISTS username,
    DROP COLUMN IF EXISTS username_norm,
    DROP COLUMN IF EXISTS last_username_change_at,
    DROP COLUMN IF EXISTS show_discord_username,
    DROP COLUMN IF EXISTS show_discord_avatar;