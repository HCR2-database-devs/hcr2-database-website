CREATE SEQUENCE ip_ban_id_seq;
CREATE TABLE ip_ban (
    id integer PRIMARY KEY DEFAULT nextval('ip_ban_id_seq'),
    banned_ip text NOT NULL,
    reason text NOT NULL,
    banned_by text NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone,
    active boolean NOT NULL DEFAULT TRUE
);
ALTER SEQUENCE ip_ban_id_seq OWNED BY ip_ban.id;

CREATE UNIQUE INDEX idx_ip_ban_active_ip ON ip_ban (banned_ip) WHERE active = TRUE;
CREATE INDEX idx_ip_ban_ip ON ip_ban (banned_ip);
CREATE INDEX idx_ip_ban_active ON ip_ban (active);
