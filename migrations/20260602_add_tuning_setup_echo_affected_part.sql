ALTER TABLE tuning_setup ADD COLUMN IF NOT EXISTS echo_affected_part_id smallint DEFAULT NULL;

COMMENT ON COLUMN tuning_setup.echo_affected_part_id IS 'ID of the tuning part that Echo (part 26) affects in this setup. NULL when Echo is not in the setup.';
