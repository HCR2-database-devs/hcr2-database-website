SET search_path = public;

ALTER TABLE tuning_setup
    DROP CONSTRAINT IF EXISTS tuning_setup_echo_part_fk,
    DROP COLUMN IF EXISTS echo_affected_part_id;
