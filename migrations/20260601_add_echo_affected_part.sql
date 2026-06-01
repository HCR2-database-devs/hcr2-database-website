ALTER TABLE pending_submission 
ADD COLUMN IF NOT EXISTS echo_affected_part_id smallint DEFAULT NULL;

COMMENT ON COLUMN pending_submission.echo_affected_part_id IS 'ID of the tuning part affected by Echo (part id 26). Only populated when Echo is selected. Cannot be: 26 (Echo), 2 (Magnet), 14 (Spoiler), 13 (Rollcage), 7 (Jump shocks), 18 (Air control), 16 (Heavyweight), 17 (Winter tires), 25 (Amplifier)';

CREATE INDEX IF NOT EXISTS idx_pending_submission_echo_affected_part ON pending_submission(echo_affected_part_id) WHERE echo_affected_part_id IS NOT NULL;
