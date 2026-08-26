CREATE SEQUENCE activity_log_id_seq;
CREATE TABLE activity_log (
    id integer PRIMARY KEY DEFAULT nextval('activity_log_id_seq'),
    admin_username text NOT NULL,
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id integer,
    entity_name text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER SEQUENCE activity_log_id_seq OWNED BY activity_log.id;

CREATE INDEX activity_log_created_at_idx ON activity_log (created_at DESC);
CREATE INDEX activity_log_admin_username_idx ON activity_log (admin_username);
CREATE INDEX activity_log_action_idx ON activity_log (action);
CREATE INDEX activity_log_entity_type_idx ON activity_log (entity_type);
