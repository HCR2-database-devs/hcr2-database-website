CREATE SEQUENCE community_user_notification_id_seq;
CREATE TABLE community_user_notification (
    id integer PRIMARY KEY DEFAULT nextval('community_user_notification_id_seq'),
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    type text NOT NULL,
    message text NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at timestamp without time zone
);
ALTER SEQUENCE community_user_notification_id_seq OWNED BY community_user_notification.id;

CREATE INDEX idx_community_user_notification_user
    ON community_user_notification (community_user_id, created_at DESC, id DESC);
CREATE INDEX idx_community_user_notification_unread
    ON community_user_notification (community_user_id) WHERE read_at IS NULL;
