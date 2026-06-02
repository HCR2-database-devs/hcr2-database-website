BEGIN;

DROP INDEX IF EXISTS pendingsubmission_map_vehicle_idx;
DROP INDEX IF EXISTS pendingsubmission_status_submitted_idx;
ALTER TABLE IF EXISTS pendingsubmission DROP CONSTRAINT IF EXISTS pendingsubmission_status_check;

DROP INDEX IF EXISTS news_created_at_id_desc_idx;

COMMIT;
