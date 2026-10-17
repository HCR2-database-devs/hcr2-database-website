CREATE TABLE longest_standing_record (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    id_record  INTEGER REFERENCES world_record(id_record) ON DELETE SET NULL,
    set_by     TEXT NOT NULL DEFAULT '',
    set_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO longest_standing_record (id) VALUES (1);