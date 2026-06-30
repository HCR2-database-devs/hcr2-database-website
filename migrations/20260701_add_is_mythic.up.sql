ALTER TABLE world_record ADD COLUMN is_mythic boolean NOT NULL DEFAULT false;

DROP INDEX IF EXISTS world_record_current_map_vehicle_unique;

CREATE UNIQUE INDEX world_record_current_map_vehicle_unique
  ON world_record (id_map, id_vehicle, is_mythic)
  WHERE current = 1;

UPDATE world_record wr
SET is_mythic = true
WHERE EXISTS (
  SELECT 1 FROM tuning_setup_part tsp
  JOIN tuning_part tp ON tp.id_tuning_part = tsp.id_tuning_part
  WHERE tsp.id_tuning_setup = wr.id_tuning_setup
  AND tp.name_tuning_part IN ('Echo', 'Amplifier')
);
