CREATE TABLE community_feature_tester (
    community_user_id integer PRIMARY KEY REFERENCES community_user (id) ON DELETE CASCADE,
    added_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    added_by_admin boolean NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_community_feature_tester_added_at
    ON community_feature_tester (added_at DESC);

INSERT INTO community_feature_tester (community_user_id, added_by_admin)
SELECT id, FALSE FROM community_user
ON CONFLICT (community_user_id) DO NOTHING;