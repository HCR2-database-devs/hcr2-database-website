SET search_path = public;

ALTER TABLE pending_submission
    DROP CONSTRAINT IF EXISTS pending_submission_echo_part_fk,
    DROP COLUMN IF EXISTS echo_affected_part_id;
