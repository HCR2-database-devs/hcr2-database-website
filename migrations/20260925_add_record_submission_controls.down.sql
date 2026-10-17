DROP TABLE IF EXISTS public_submission_rate_limit;

DROP INDEX IF EXISTS world_record_submitter_community_user_idx;
ALTER TABLE world_record
    DROP CONSTRAINT IF EXISTS world_record_submitter_community_user_fk;
ALTER TABLE world_record
    DROP COLUMN IF EXISTS submitter_community_user_id;

DROP INDEX IF EXISTS pending_submission_submitter_community_user_idx;
ALTER TABLE pending_submission
    DROP CONSTRAINT IF EXISTS pending_submission_submitter_community_user_fk;
ALTER TABLE pending_submission
    DROP COLUMN IF EXISTS submitter_community_user_id;

UPDATE pending_submission
SET submitter_ip = ''
WHERE submitter_ip IS NULL;

ALTER TABLE pending_submission
    ALTER COLUMN submitter_ip SET NOT NULL;
