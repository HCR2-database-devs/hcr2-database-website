ALTER TABLE world_record ADD COLUMN created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX world_record_history_idx ON world_record (id_map, id_vehicle, is_mythic, id_record);