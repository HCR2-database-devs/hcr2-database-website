CREATE SEQUENCE map_id_seq;
CREATE TABLE map (
    id_map integer PRIMARY KEY DEFAULT nextval('map_id_seq'),
    name_map text NOT NULL UNIQUE,
    special integer NOT NULL DEFAULT 0 CHECK (special IN (0, 1))
);
ALTER SEQUENCE map_id_seq OWNED BY map.id_map;

CREATE SEQUENCE vehicle_id_seq;
CREATE TABLE vehicle (
    id_vehicle integer PRIMARY KEY DEFAULT nextval('vehicle_id_seq'),
    name_vehicle text NOT NULL UNIQUE
);
ALTER SEQUENCE vehicle_id_seq OWNED BY vehicle.id_vehicle;

CREATE SEQUENCE player_id_seq;
CREATE TABLE player (
    id_player integer PRIMARY KEY DEFAULT nextval('player_id_seq'),
    name_player text NOT NULL UNIQUE,
    country text NOT NULL DEFAULT ''
);
ALTER SEQUENCE player_id_seq OWNED BY player.id_player;

CREATE SEQUENCE tuning_part_id_seq;
CREATE TABLE tuning_part (
    id_tuning_part integer PRIMARY KEY DEFAULT nextval('tuning_part_id_seq'),
    name_tuning_part text NOT NULL UNIQUE
);
ALTER SEQUENCE tuning_part_id_seq OWNED BY tuning_part.id_tuning_part;

CREATE SEQUENCE tuning_setup_id_seq;
CREATE TABLE tuning_setup (
    id_tuning_setup integer PRIMARY KEY DEFAULT nextval('tuning_setup_id_seq')
);
ALTER SEQUENCE tuning_setup_id_seq OWNED BY tuning_setup.id_tuning_setup;

CREATE TABLE tuning_setup_part (
    id_tuning_setup integer NOT NULL,
    id_tuning_part integer NOT NULL,
    CONSTRAINT tuning_setup_part_pkey PRIMARY KEY (id_tuning_setup, id_tuning_part),
    CONSTRAINT tuning_setup_part_setup_fk
        FOREIGN KEY (id_tuning_setup)
        REFERENCES tuning_setup (id_tuning_setup)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT tuning_setup_part_part_fk
        FOREIGN KEY (id_tuning_part)
        REFERENCES tuning_part (id_tuning_part)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE SEQUENCE world_record_id_seq;
CREATE TABLE world_record (
    id_record integer PRIMARY KEY DEFAULT nextval('world_record_id_seq'),
    id_map integer NOT NULL,
    id_vehicle integer NOT NULL,
    id_player integer NOT NULL,
    distance integer NOT NULL CHECK (distance > 0),
    current integer NOT NULL DEFAULT 1,
    id_tuning_setup integer,
    questionable integer NOT NULL DEFAULT 0,
    questionable_reason text,
    CONSTRAINT world_record_current_check CHECK (current IN (0, 1)),
    CONSTRAINT world_record_questionable_check CHECK (questionable IN (0, 1)),
    CONSTRAINT world_record_map_fk
        FOREIGN KEY (id_map)
        REFERENCES map (id_map)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT world_record_vehicle_fk
        FOREIGN KEY (id_vehicle)
        REFERENCES vehicle (id_vehicle)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT world_record_player_fk
        FOREIGN KEY (id_player)
        REFERENCES player (id_player)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT world_record_tuning_setup_fk
        FOREIGN KEY (id_tuning_setup)
        REFERENCES tuning_setup (id_tuning_setup)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);
ALTER SEQUENCE world_record_id_seq OWNED BY world_record.id_record;

CREATE UNIQUE INDEX world_record_current_map_vehicle_unique
    ON world_record (id_map, id_vehicle)
    WHERE current = 1;
CREATE INDEX world_record_current_idx ON world_record (current);
CREATE INDEX world_record_map_vehicle_idx ON world_record (id_map, id_vehicle);

CREATE SEQUENCE pending_submission_id_seq;
CREATE TABLE pending_submission (
    id integer PRIMARY KEY DEFAULT nextval('pending_submission_id_seq'),
    id_map integer NOT NULL,
    id_vehicle integer NOT NULL,
    distance integer NOT NULL CHECK (distance > 0),
    player_name text NOT NULL,
    player_country text NOT NULL DEFAULT '',
    submitter_ip text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'pending',
    submitted_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tuning_parts text,
    CONSTRAINT pending_submission_status_check
        CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT pending_submission_map_fk
        FOREIGN KEY (id_map)
        REFERENCES map (id_map)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT pending_submission_vehicle_fk
        FOREIGN KEY (id_vehicle)
        REFERENCES vehicle (id_vehicle)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
ALTER SEQUENCE pending_submission_id_seq OWNED BY pending_submission.id;

CREATE INDEX pending_submission_status_submitted_idx
    ON pending_submission (status, submitted_at DESC, id DESC);
CREATE INDEX pending_submission_map_vehicle_idx
    ON pending_submission (id_map, id_vehicle);
CREATE INDEX pending_submission_submitter_time_idx
    ON pending_submission (submitter_ip, submitted_at);

CREATE SEQUENCE news_id_seq;
CREATE TABLE news (
    id integer PRIMARY KEY DEFAULT nextval('news_id_seq'),
    title text NOT NULL,
    content text NOT NULL,
    author text,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER SEQUENCE news_id_seq OWNED BY news.id;

CREATE INDEX news_created_at_id_desc_idx ON news (created_at DESC, id DESC);
