DROP INDEX IF EXISTS world_record_history_idx;

DELETE FROM world_record WHERE current = 0;

ALTER TABLE world_record DROP COLUMN created_at;