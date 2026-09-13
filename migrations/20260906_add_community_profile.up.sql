ALTER TABLE community_user
    ADD COLUMN bio text NOT NULL DEFAULT '',
    ADD COLUMN country text,
    ADD COLUMN favorite_vehicle_id integer REFERENCES vehicle (id_vehicle) ON DELETE SET NULL,
    ADD COLUMN favorite_map_id integer REFERENCES map (id_map) ON DELETE SET NULL,
    ADD COLUMN banner_content bytea,
    ADD COLUMN banner_content_type text,
    ADD COLUMN banner_updated_at timestamp without time zone,
    ADD COLUMN profile_public boolean NOT NULL DEFAULT TRUE,
    ADD COLUMN show_country boolean NOT NULL DEFAULT FALSE,
    ADD COLUMN show_bio boolean NOT NULL DEFAULT FALSE,
    ADD COLUMN show_favorite_vehicle boolean NOT NULL DEFAULT FALSE,
    ADD COLUMN show_favorite_map boolean NOT NULL DEFAULT FALSE,
    ADD COLUMN admin_disabled boolean NOT NULL DEFAULT FALSE;

CREATE INDEX idx_community_user_updated_at ON community_user (updated_at);

CREATE SEQUENCE community_profile_report_id_seq;
CREATE TABLE community_profile_report (
    id integer PRIMARY KEY DEFAULT nextval('community_profile_report_id_seq'),
    community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    reporter_community_user_id integer NOT NULL REFERENCES community_user (id) ON DELETE CASCADE,
    category text NOT NULL,
    reason text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'open',
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_by text,
    resolved_at timestamp without time zone,
    resolution_note text
);
ALTER SEQUENCE community_profile_report_id_seq OWNED BY community_profile_report.id;

CREATE UNIQUE INDEX uq_community_profile_report_open
    ON community_profile_report (community_user_id, reporter_community_user_id)
    WHERE status = 'open';
CREATE INDEX idx_community_profile_report_status ON community_profile_report (status);
CREATE INDEX idx_community_profile_report_created_at ON community_profile_report (created_at DESC);

ALTER TABLE activity_log ADD COLUMN note text;